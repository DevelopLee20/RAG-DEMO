import hashlib
import os

from fastapi import UploadFile
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from typing import AsyncGenerator
from app.db.text_db import find_safe_name_by_name, read_text_db, write_text_db
from app.db.vector_db import create_vector_store, select_vector_store
from app.utils.langchain_util import create_chunks_to_text, use_chain_clovaX, get_chain_clovaX
from app.utils.pdf_util import parse_pdf, save_pdf


async def file_upload_service(file: UploadFile) -> tuple[int, str]:
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
    parse_text = await parse_pdf(file=file)

    # PDF 저장
    await save_pdf(file=file, safe_name=safe_folder_name)

    # 청킹
    documents = await create_chunks_to_text(parse_text)

    # 텍스트 디비에 이름, 안전 이름 쌍 저장
    await write_text_db(file_basename, safe_folder_name)

    await create_vector_store(name=safe_folder_name, chunks=documents)

    return HTTP_200_OK, "저장 성공"


async def chat_service(name: str, query: str) -> tuple[int, str]:
    """채팅 서비스

    Args:
        name (str): 벡터 스토어 이름
        query (str): 질문

    Returns:
        tuple[int, str]: 상태코드와 메시지
    """

    safe_name = await find_safe_name_by_name(name=name)
    vector_store = await select_vector_store(name=safe_name)

    if vector_store is None:
        return HTTP_404_NOT_FOUND, "벡터 스토어가 존재하지 않습니다."

    chunk = vector_store.similarity_search(query=query)

    # Chat 기능
    result = await use_chain_clovaX(chunk=chunk, query=query)

    # 반환
    return HTTP_200_OK, result


async def get_pdf_file_list() -> tuple[int, str, list[str]]:
    db_data = await read_text_db()
    file_names = [item[0] for item in db_data]

    return HTTP_200_OK, "리스트 조회 성공", file_names


async def chat_stream_service(name: str, query: str) -> AsyncGenerator[str, None]:
    chain = await get_chain_clovaX()
    safe_name = await find_safe_name_by_name(name=name)
    vector_store = await select_vector_store(name = safe_name)
    chunk = vector_store.similarity_search(query = query)

    async for event in chain.astream(
        {
            "results" : chunk, 
            "query" : query,
        }
    ):
        if event and hasattr(event, "content"):
            yield f"data: {event.content}\n\n"

    yield "data: [DONE]\n\n"
     
