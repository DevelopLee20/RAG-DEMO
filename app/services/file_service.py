import asyncio
import hashlib
import os
from collections.abc import AsyncGenerator

from fastapi import UploadFile
from langchain_community.chat_message_histories import ChatMessageHistory
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from app.db.text_db import (
    delete_text_db,
    find_safe_name_by_name,
    read_text_db,
    write_text_db,
)
from app.db.vector_db import (
    create_vector_store,
    delete_vector_store,
    select_vector_store,
)
from app.utils.langchain_util import (
    add_to_history,
    create_chunks_to_text,
    get_chain_clovaX,
    get_langfuse_handler,
    use_chain_clovaX,
)
from app.utils.pdf_util import parse_pdf, save_pdf

UPLOAD_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "uploaded_files")
)

# 채팅 히스토리 저장용
store = {}


def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


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


async def file_delete_service(name: str) -> tuple[int, str]:
    """파일 삭제 서비스

    Args:
        name (str): 파일 이름

    Returns:
        tuple[int, str]: 상태 코드와 메시지
    """
    safe_name = await find_safe_name_by_name(name=name)
    if not safe_name:
        return HTTP_404_NOT_FOUND, "파일 이름이 존재하지 않습니다."

    file_path = os.path.join(UPLOAD_DIRECTORY, f"{safe_name}.pdf")
    if os.path.exists(file_path):
        os.remove(file_path)

    await delete_vector_store(name=safe_name)
    await delete_text_db(name=name)

    return HTTP_200_OK, "삭제 성공"


async def chat_service(
    name: str, query: str, session_id: str = "default"
) -> tuple[int, str]:
    """채팅 서비스

    Args:
        name (str): 벡터 스토어 이름
        query (str): 질문
        session_id (str): 세션 ID

    Returns:
        tuple[int, str]: 상태코드와 메시지
    """

    safe_name = await find_safe_name_by_name(name=name)
    vector_store = await select_vector_store(name=safe_name)

    if vector_store is None:
        return HTTP_404_NOT_FOUND, "벡터 스토어가 존재하지 않습니다."

    chunk = vector_store.similarity_search(query=query)

    # AI 응답 생성
    result = await use_chain_clovaX(chunk=chunk, query=query)

    # 히스토리에 추가
    await add_to_history(session_id=session_id, query=query, response=result)

    # 반환
    return HTTP_200_OK, result


async def get_pdf_file_list() -> tuple[int, str, list[str]]:
    db_data = await read_text_db()
    file_names = [item[0] for item in db_data]

    return HTTP_200_OK, "리스트 조회 성공", file_names


async def get_file_path_service(name: str) -> str | None:
    file_basename, _ = os.path.splitext(name)
    safe_name = await find_safe_name_by_name(name=file_basename)
    if not safe_name:
        return None

    file_path = os.path.join(UPLOAD_DIRECTORY, f"{safe_name}.pdf")
    if os.path.exists(file_path):
        return file_path
    return None


async def chat_stream_service(
    name: str, query: str, session_id: str
) -> AsyncGenerator[str, None]:
    """스트리밍 채팅 서비스

    Args:
        name (str): 벡터 스토어 이름
        query (str): 질문
        session_id (str): 세션 ID

    Yields:
        str: 스트리밍 응답 데이터
    """
    safe_name = await find_safe_name_by_name(name=name)
    vector_store = await select_vector_store(name=safe_name)
    chain = await get_chain_clovaX()

    if vector_store is None:
        yield "data: 선택한 파일의 벡터 스토어가 존재하지 않습니다. 파일을 다시 선택하거나 업로드하세요.\n\n"
        yield "data: [DONE]\n\n"
        return

    chunk = vector_store.similarity_search(query=query)

    # 세션 히스토리 가져오기
    history = get_session_history(session_id)
    # 사용자 질의 저장
    history.add_user_message(query)

    # 스트리밍 응답 누적 버퍼
    accumulated_content: list[str] = []

    # 핸들러 불러오기
    handler = await get_langfuse_handler()

    async for event in chain.astream(
        {
            "results": chunk,
            "query": query,
        },
        config={
            "callbacks": [handler],
        },
    ):
        if event and hasattr(event, "content"):
            for text in event.content:
                for t in text:
                    yield f"data: {t}\n\n"
                    await asyncio.sleep(0.02)

            # yield f"data: {event.content}\n\n"

    # ai 답변 저장 (전체 내용)
    full_content = "".join(accumulated_content)
    if full_content:
        await add_to_history(session_id=session_id, query=query, response=full_content)

    yield "data: [DONE]\n\n"
