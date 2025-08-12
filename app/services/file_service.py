import os

from fastapi import UploadFile
from starlette.status import HTTP_200_OK

from app.db.vector_db import create_vector_store
from app.utils.langchain_util import create_chunks_to_text
from app.utils.pdf_util import parse_pdf


async def file_upload_service(file: UploadFile) -> tuple[int, str]:
    # PDF 파싱
    parse_text = await parse_pdf(file=file)

    # 청킹
    documents = await create_chunks_to_text(parse_text)

    # 벡터 베이스에 저장
    file_basename, _ = os.path.splitext(file.filename)
    await create_vector_store(name=file_basename, chunks=documents)

    return HTTP_200_OK, "저장 성공"
