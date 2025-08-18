import asyncio
from collections.abc import AsyncGenerator

from langchain_community.chat_message_histories import ChatMessageHistory
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from app.db.text_db import TextDB
from app.db.vector_db import VectorDB
from app.utils.langchain_util import LangchainUtil
from app.utils.langfuse_util import LangfuseUtil


class ChatService:
    @classmethod
    async def chat_service(
        cls, name: str, query: str, session_id: str = "default"
    ) -> tuple[int, str]:
        """채팅 서비스

        Args:
            name (str): 벡터 스토어 이름
            query (str): 질문
            session_id (str): 세션 ID

        Returns:
            tuple[int, str]: 상태코드와 메시지
        """

        # 안전한 이름 검색
        safe_name = await TextDB.find_safe_name_by_name(name=name)

        # 벡터 스토어 검색
        vector_store = await VectorDB.select_vector_store(name=safe_name)
        if vector_store is None:
            return HTTP_404_NOT_FOUND, "벡터 스토어가 존재하지 않습니다."

        # 청크 검색
        chunk = vector_store.similarity_search(query=query)

        # AI 응답 생성
        result = await LangchainUtil.use_chain_clovaX(chunk=chunk, query=query)

        # 히스토리에 추가
        await LangchainUtil.add_to_history(
            session_id=session_id, query=query, response=result
        )

        # 반환
        return HTTP_200_OK, result

    @classmethod
    async def chat_stream_service(
        cls, name: str, query: str, session_id: str
    ) -> AsyncGenerator[str, None]:
        """스트리밍 채팅 서비스

        Args:
            name (str): 벡터 스토어 이름
            query (str): 질문
            session_id (str): 세션 ID

        Yields:
            str: 스트리밍 응답 데이터
        """
        safe_name = await TextDB.find_safe_name_by_name(name=name)
        vector_store = await VectorDB.select_vector_store(name=safe_name)
        chain = await LangchainUtil.get_chain_clovaX()

        if vector_store is None:
            yield "data: 선택한 파일의 벡터 스토어가 존재하지 않습니다. 파일을 다시 선택하거나 업로드하세요.\n\n"
            yield "data: [DONE]\n\n"
            return

        # 유사 청크 검색
        chunk = vector_store.similarity_search(query=query)

        # 세션 히스토리 가져오기
        history: ChatMessageHistory = await LangchainUtil.get_session_history(
            session_id
        )
        # 사용자 질의 저장
        history.add_user_message(query)

        # 스트리밍 응답 누적 버퍼
        accumulated_content: list[str] = []

        # 핸들러 불러오기
        handler = await LangfuseUtil.get_langfuse_handler(tags=["RAG"])

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

        await LangchainUtil.evalate_llm_score(
            query=query, answer=event.content, context=chunk
        )

        # ai 답변 저장 (전체 내용)
        full_content = "".join(accumulated_content)
        if full_content:
            await LangchainUtil.add_to_history(
                session_id=session_id, query=query, response=full_content
            )

        yield "data: [DONE]\n\n"
