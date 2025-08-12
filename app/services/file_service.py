import hashlib
import os

from fastapi import UploadFile
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from app.db.vector_db import create_vector_store, select_vector_store
from app.utils.langchain_util import create_chunks_to_text, use_chain_clovaX
from app.utils.pdf_util import parse_pdf


async def file_upload_service(file: UploadFile) -> tuple[int, str]:
    # PDF 파싱
    parse_text = await parse_pdf(file=file)

    # 청킹
    documents = await create_chunks_to_text(parse_text)

    # 벡터 베이스에 저장
    file_basename, _ = os.path.splitext(file.filename)
    safe_folder_name = hashlib.sha256(file_basename.encode("utf-8")).hexdigest()

    await create_vector_store(name=safe_folder_name, chunks=documents)

    return HTTP_200_OK, "저장 성공"


async def chat_service(name: str, query: str) -> tuple[int, str]:
    vector_store = await select_vector_store(name=name)

    if vector_store is None:
        return HTTP_404_NOT_FOUND, "벡터 스토어가 존재하지 않습니다."

    chunk = vector_store.similarity_search(query=query)

    # Chat 기능
    result = await use_chain_clovaX(chunk=chunk, query=query)

    # 반환
    return HTTP_200_OK, result
