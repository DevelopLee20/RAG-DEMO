from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_naver import ChatClovaX, ClovaXEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langfuse.callback import CallbackHandler
from langfuse import Langfuse
import re

from app.core.env import (
    CLOVASTUDIO_API_TOKEN,
    LANGFUSE_HOST,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
)

splitter = None
embedding = None
chain_clovaX = None
clovaX = None
langfuseHandlers = {}
langfuse = None

# 채팅 히스토리 저장용
store = {}


def get_session_history(session_id: str) -> ChatMessageHistory:
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
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

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
            model="HCX-005",
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
                    1. [Context]를 참고해서 사용자의 질문에 대한 답을 생성해주세요.
                    2. 1에서 생성한 답이 문서에 존재하는지 검토 후 답변해주세요.
                    3. 2에서 생성한 답이 질문에 대한 올바른 대답인지 검토 후 답변해주세요.

                    조건
                    - 가능한 단답형으로 대답해주세요.
                    - 만약 3에서 생성한 답이 문서에 존재하지 않는다면 "문서에 없음" 이라고 답변해주세요.

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


async def get_langfuse_handler(session_id: str) -> CallbackHandler:
    """랭퓨즈 클라이언트 반환 함수

    Args:
        session_id (str): 세션 ID

    Returns:
        CallbackHandler: 랭퓨즈 클라이언트 객체
    """
    global langfuseHandlers

    if session_id not in langfuseHandlers:
        langfuseHandlers[session_id] = CallbackHandler(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
            session_id=session_id
        )

    return langfuseHandlers[session_id]


async def use_chain_clovaX(chunk: list[Document], query: str, session_id: str) -> str:
    """체이닝된 클로바엑스 객체 사용 함수

    Args:
        chunk (list[Document]): 가장 유사도 높은 청크
        query (str): 질문
        session_id (str): 세션 ID

    Returns:
        str: 질문에 대한 대답
    """
    chain = await get_chain_clovaX()
    langfuseHandler = await get_langfuse_handler(session_id)

    result = await chain.ainvoke(
        {
            "results": chunk,
            "query": query,
        },
        config={"callbacks": [langfuseHandler]},
    )
    return result.content


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


async def get_llm_score(trace_id: str, chunk : list[Document], query: str, response: str):
    """생성된 대화 내역에 대한 평가 점수를 저장하는 함수
    
    """
    global langfuse
    
    if langfuse is None:
        langfuse = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )

    trace = langfuse.trace(id=trace_id)

    # Langfuse v2에서는 generation 대신 span을 사용
    span = trace.span(
        name="auto evaluation", 
        input=query, 
        output=response
    )

    # LLM을 사용한 자동 평가
    evaluation_score = await evaluate_response_with_llm(chunk, query, response)
    
    # 평가 점수를 Langfuse에 저장
    trace.score(
        name="correctness",
        value=evaluation_score,
        comment="LLM-based auto-evaluated correctness score"
    )

async def create_langfuse_dataset(db_name: str):
    # langfuse 데이터셋 생성
    langfuse.create_dataset(
        name = db_name, 
        description = "데이터 테스트셋"
    )

# LLM as Judgement 
async def evaluate_response_with_llm(chunk : list[Document], query: str, response: str) -> float:
    """LLM을 사용하여 응답을 평가하는 함수
    
    Args:
        query (str): 사용자 질문
        response (str): AI 응답
        
    Returns:
        float: 0.0~1.0 사이의 평가 점수
    """
    try:
        clova_model = await get_clovaX()
        
        # 직접 메시지 형식으로 평가 요청
        evaluation_messages = [
            {"role": "system", "content": """당신은 AI 응답의 품질을 평가하는 전문가입니다. 
            문서에서 찾은 내용이 근거로서 적절히 사용되었는지 참고하여 평가해주세요.
        
다음 기준으로 0.0~1.0 사이의 점수를 매겨주세요:
- 0.0-0.3: 응답이 질문과 전혀 관련없거나 잘못된 정보
- 0.4-0.6: 부분적으로 관련있지만 불완전한 응답
- 0.7-0.8: 질문에 적절히 답변하지만 개선 여지가 있음
- 0.9-1.0: 질문에 완벽하게 답변하고 정확한 정보 제공

점수만 숫자로 응답해주세요 (예: 0.8)."""},
            {"role": "user", "content": f"질문: {query}\n응답: {response}\n 참고: {chunk}\n\n점수:"}
        ]
        
        result = await clova_model.ainvoke(evaluation_messages)
        
        score_text = result.content.strip()
        
        # 숫자 추출
        score_match = re.search(r'0\.\d+', score_text)
        if score_match:
            score = float(score_match.group())
            return min(max(score, 0.0), 1.0)  # 0.0~1.0 범위로 제한
        else:
            return 0.5  # 기본값
    except Exception as e:
        print(f"평가 중 오류 발생: {e}")
        return 0.5  # 오류 시 기본값


