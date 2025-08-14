from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_naver import ChatClovaX, ClovaXEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.chat_message_histories import ChatMessageHistory
from langfuse.callback import CallbackHandler
from langfuse import Langfuse
from collections.abc import AsyncGenerator
import os

from app.core.env import CLOVASTUDIO_API_TOKEN, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST, LANGFUSE_PROJECT_ID, LANGFUSE_ORG_ID

splitter = None
embedding = None
chain_clovaX = None
clovaX = None

langfuseHandler = CallbackHandler(
  secret_key=LANGFUSE_SECRET_KEY,
  public_key=LANGFUSE_PUBLIC_KEY,
  host=LANGFUSE_HOST
)

# 채팅 히스토리 저장용
store = {} 

def get_session_history(session_id : str) -> ChatMessageHistory:
    """세션 히스토리를 가져오는 함수
    
    Args:
        session_id (str): 세션 ID
        
    Returns:
        ChatMessageHistory: 세션 히스토리 객체
    """
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def get_splitter() -> RecursiveCharacterTextSplitter:
    """텍스트 파싱 스플리터 객체 반환

    Returns:
        RecursiveCharacterTextSplitter: 스플리터 객체
    """
    global splitter

    if splitter is None:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)

    return splitter

async def create_chunks_to_text(texts: list[str]) -> list[Document]:
    """텍스트를 받아서 청크 리스트를 생성하는 함수

    Args:
        texts (list[str]): 텍스트 리스트

    Returns:
        list[Document]: 청크 리스트 객체
    """
    return get_splitter().create_documents(texts=texts)

async def get_embedding() -> ClovaXEmbeddings:
    """임베딩을 반환하는 함수

    Returns:
        ClovaXEmbeddings: 생성된 임베딩
    """
    global embedding

    if embedding is None:
        embedding = ClovaXEmbeddings(
            model="bge-m3",
            dimensions=1024,
            api_key=CLOVASTUDIO_API_TOKEN,
        )

    return embedding

async def get_clovaX() -> ChatClovaX:
    """클로바엑스 객체 반환 함수

    Returns:
        ChatClovaX: 클로바엑스 객체
    """
    global clovaX

    if clovaX is None:
        clovaX = ChatClovaX(
            model="HCX-003",
            max_tokens=128,
            api_key=CLOVASTUDIO_API_TOKEN,
        )

    return clovaX

async def get_chain_clovaX():
    """클로바엑스 프롬프트 체인 객체 반환 함수

    Returns:
        Chain: 모델과 프롬프트 체인 객체
    """
    global chain_clovaX

    if chain_clovaX is None:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """아래 순서에 따라 사용자의 질문에 답변해주세요.
                    1. [Context]를 참고해서 사용자의 질문에 대한 답을 생성
                    2. 1에서 생성한 답이 질문에 대한 올바른 답인지 검토 후 답변

                    조건
                    - 가능한 단답형으로 대답해주세요.

                    [Context]
                    {results}
                    """,
                ),
                ("human", "질문: {query}"),
            ]
        )

        clova_model = await get_clovaX()
        chain_clovaX = prompt | clova_model

    return chain_clovaX

async def use_chain_clovaX(chunk: list[Document], query: str) -> str:
    """체이닝된 클로바엑스 객체 사용 함수

    Args:
        chunk (list[Document]): 가장 유사도 높은 청크
        query (str): 질문

    Returns:
        str: 질문에 대한 대답
    """
    chain = await get_chain_clovaX()

    result = await chain.ainvoke(
        {
            "results": chunk,
            "query": query,
        },
        config = {
            "callbacks": [langfuseHandler]
        }
        
    )
    return result.content

async def stream_chain_clovaX_raw(chunk: list[Document], query: str) -> AsyncGenerator[str, None]:
    """스트리밍 방식으로 체이닝된 클로바엑스 객체 사용 함수 (원시 텍스트 반환)

    Args:
        chunk (list[Document]): 가장 유사도 높은 청크
        query (str): 질문

    Yields:
        str: 원시 텍스트 응답
    """
    chain = await get_chain_clovaX()
    
    async for event in chain.astream(
        {
            "results": chunk,
            "query": query,
        },
        config={
            "callbacks": [langfuseHandler]
        }
    ):
        if event and hasattr(event, "content"):
            yield event.content

async def add_to_history(session_id: str, query: str, response: str):
    """세션 히스토리에 대화 내용을 추가하는 함수

    Args:
        session_id (str): 세션 ID
        query (str): 사용자 질문
        response (str): AI 응답
    """
    history = get_session_history(session_id)
    history.add_user_message(query)
    history.add_ai_message(response)

