import hashlib
import os

from fastapi import UploadFile
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.db.text_db import TextDB
from app.db.vector_db import VectorDB
from app.utils.langchain_util import LangchainUtil
from app.utils.pdf_util import PdfUtil


class FileService:
    @classmethod
    async def file_upload_service(cls, file: UploadFile) -> tuple[int, str]:
        """파일 업로드 서비스

        Args:
            file (UploadFile): 업로드된 파일 객체

        Returns:
            tuple[int, str]: 상태 코드와 메시지
        """
        # 저장 이름 설정
        file_basename, _ = os.path.splitext(file.filename)
        safe_folder_name = hashlib.sha256(file_basename.encode("utf-8")).hexdigest()

        # PDF 파싱
        parse_text = await PdfUtil.parse_pdf(file=file)

        # PDF 저장
        await PdfUtil.save_pdf(file=file, safe_name=safe_folder_name)

        # 청킹
        documents = await LangchainUtil.create_chunks_to_text(parse_text)

        # 텍스트 디비에 이름, 안전 이름 쌍 저장
        await TextDB.write_text_db(file_basename, safe_folder_name)

        await VectorDB.create_vector_store(name=safe_folder_name, chunks=documents)

        return HTTP_200_OK, "저장 성공"

    @classmethod
    async def file_delete_service(cls, name: str) -> tuple[int, str]:
        """파일 삭제 서비스

        Args:
            name (str): 파일 이름

        Returns:
            tuple[int, str]: 상태 코드와 메시지
        """
        # 파일의 안전한 이름 찾기
        safe_name = await TextDB.find_safe_name_by_name(name=name)
        if not safe_name:
            return HTTP_404_NOT_FOUND, "파일 이름이 존재하지 않습니다."

        # 파일 삭제 시도
        delete_result = await PdfUtil.delete_pdf(safe_name=safe_name)
        if not delete_result:
            return HTTP_500_INTERNAL_SERVER_ERROR, "파일 삭제 중 문제 발생"

        # 벡터 스토어 삭제
        await VectorDB.delete_vector_store(name=safe_name)

        # 텍스트 디비 삭제
        await TextDB.delete_text_db(name=name)

        return HTTP_200_OK, "삭제 성공"

    @classmethod
    async def file_list_get_service(cls) -> tuple[int, str, list[str]]:
        status_code, detail, file_names = await PdfUtil.get_pdf_list()

        return status_code, detail, file_names

    @classmethod
    async def file_path_get_service(cls, name: str) -> str | None:
        file_basename, _ = os.path.splitext(name)
        safe_name = await TextDB.find_safe_name_by_name(name=file_basename)
        if not safe_name:
            return None

        path = await PdfUtil.select_pdf(safe_name=safe_name)

        return path
