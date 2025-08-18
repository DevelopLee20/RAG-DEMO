import os
import shutil
from typing import Any

import PyPDF2
from fastapi import UploadFile
from starlette.status import HTTP_200_OK

from app.db.text_db import TextDB
from app.utils.text_util import TextUtil


class PdfUtil:
    UPLOAD_DIRECTORY = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "uploaded_files")
    )

    @classmethod
    async def parse_pdf(cls, file: str | UploadFile) -> list[str]:
        """pdf 파일 또는 UploadFile 스트림을 받아서 파싱 리스트 반환

        Args:
            file (str): 파일명 또는 파일 스트림 객체

        Returns:
            list[str]: 파싱 리스트 반환
        """
        parse_list = []

        pdf: Any
        # file의 타입에 따라 형식 변경
        if isinstance(file, str):
            pdf = file
        else:
            await file.seek(0)
            pdf = file.file

        for page in PyPDF2.PdfReader(pdf).pages:
            text = page.extract_text()
            processed_text = TextUtil.preprocessing_text(text=text)

            parse_list.append(processed_text)

        # 다른 함수에서 파일을 다시 읽을 수 있도록 파일 포인터를 초기화합니다.
        if not isinstance(file, str):
            await file.seek(0)

        return parse_list

    @classmethod
    async def save_pdf(cls, file: UploadFile, safe_name: str) -> None:
        """UploadFile 객체를 서버에 저장

        Args:
            file (UploadFile): 업로드된 파일 객체
            safe_name (str): 저장될 파일명
        """
        os.makedirs(cls.UPLOAD_DIRECTORY, exist_ok=True)
        file_path = os.path.join(cls.UPLOAD_DIRECTORY, safe_name)

        # 다른 함수에서 파일을 읽었을 수 있으므로 파일 포인터를 초기화합니다.
        await file.seek(0)
        with open(file_path + ".pdf", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    @classmethod
    async def delete_pdf(cls, safe_name: str) -> bool:
        file_path = os.path.join(cls.UPLOAD_DIRECTORY, f"{safe_name}.pdf")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)

            return True
        except:
            return False

    @classmethod
    async def get_pdf_list(cls) -> tuple[int, str, list[str]]:
        db_data = await TextDB.read_text_db()
        file_names = [item[0] for item in db_data]

        return HTTP_200_OK, "리스트 조회 성공", file_names

    @classmethod
    async def select_pdf(cls, safe_name: str) -> str | None:
        file_path = os.path.join(cls.UPLOAD_DIRECTORY, f"{safe_name}.pdf")

        if os.path.exists(file_path):
            return file_path

        return None
