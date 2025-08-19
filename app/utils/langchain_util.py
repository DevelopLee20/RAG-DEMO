from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_naver import ChatClovaX, ClovaXEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langfuse.callback import CallbackHandler
from langfuse import Langfuse
import re
import asyncio

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


async def use_chain_clova_stream(chunk : list[Document], query : str, session_id : str):
    """ 클로바 랭체인 스트리밍 형식 출력 함수

    Args:
          chunk (list[Document]): 가장 유사도 높은 청크
          query (str): 질문
          session_id: 세션 ID

    Returns:
        
    """
    chain = await get_chain_clovaX()
    langfuseHandler = await get_langfuse_handler(session_id)
    
    accumulated_content: list[str] = []
    async for event in chain.astream(
        {
            "results": chunk,
            "query": query,
        },
        config={
            "callbacks": [langfuseHandler],
        },
    ) :
        if event and hasattr(event, "content"):
            accumulated_content.append(event.content)
            yield f"data: {event.content}\n\n"  # SSE 메시지 포맷
            await asyncio.sleep(0.02)


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

async def create_langfuse_dataset(db_name: str):
    # langfuse 데이터셋 생성
    langfuse.create_dataset(
        name = db_name, 
        description = "데이터 테스트셋"
    )

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

    # LLM을 사용한 자동 평가 (점수와 평가 이유 함께 반환)
    print(f"\n{'='*60}")
    print(f"Trace ID: {trace_id}")
    print(f"질문: {query}")
    print(f"응답: {response}")
    print(f"{'='*60}")
    
    evaluation_result = await evaluate_response_with_llm(chunk, query, response)
    evaluation_score = evaluation_result["score"]
    evaluation_reason = evaluation_result["reason"]
    
    # 평가 결과 로그
    print(f"   점수: {evaluation_score:.2f}/1.0")
    print(f"   평가 이유: {evaluation_reason}")
    print(f"{'='*60}\n")
    
    # 평가 점수와 이유를 Langfuse에 저장
    trace.score(
        name="correctness",
        value=evaluation_score,
        comment=evaluation_reason
    )

    return evaluation_score

# LLM as Judgement 
async def evaluate_response_with_llm(chunk : list[Document], query: str, response: str) -> dict:
    """LLM을 사용하여 응답을 평가하는 함수
    
    Args:
        chunk (list[Document]): 참고 문서
        query (str): 사용자 질문
        response (str): AI 응답
        
    Returns:
        dict: {"score": float, "reason": str} - 평가 점수와 이유
    """

    try:
        clova_model = await get_clovaX()
        
        # 직접 메시지 형식으로 평가 요청
        evaluation_messages = [
        {"role": "system", "content": """당신은 RAG 응답의 품질을 평가하는 전문가입니다. 
        질문과 RAG 응답, 그리고 참고 문서를 기반으로 응답 품질을 점수화해주세요.
        
        - 사용자 질문 : {query}
        - RAG 모델 응답 : {response}
        - 참고 자료 : {chunk}

        다음 기준을 따라 평가하세요:

            1. 질문에 대한 **정확한 정보가 문서에 포함되어 있는 경우**, 모델 응답이 해당 정보를 **정확히 반영하고 왜곡 없이 요약 또는 인용했는지** 평가하세요.

            2. 질문에 대한 정보가 **문서에 존재하지 않는 경우**, 아래 두 가지 중 하나면 정확한 응답으로 간주하고 **정확도 점수 1.00**을 부여하세요:
            - 모델이 "문서에 없음" 또는 이와 동등한 표현으로 답한 경우
            - 모델이 **응답하지 않았으며**, 이는 문서에 정보가 없기 때문이라고 판단되는 경우

            3. 반대로, 문서에 정보가 없음에도 불구하고 모델이 **추측으로 답변한 경우**, 정확도 점수는 낮아야 합니다 (예: 0.0 ~ 0.3).
            
        응답 형식:
            점수: [0.0~1.0 사이 숫자]
            평가 이유: [점수를 매긴 구체적 이유와 근거, 2~3문장]

        예시:
            점수: 0.8
            평가 이유: 응답이 질문과 관련성이 높고, 문서 근거를 참조했으나, 일부 세부 정보가 누락되어 완전한 답변은 아님.
            
        예시 : 
            점수 : 1.0
            평가 이유: 질문에 대해 참고 문서에서 답을 찾을 수 없음을 명확히 알렸음. 문서 근거가 없다는 사실을 정확히 안내했으므로 완벽한 대응으로 평가됨.    
        """},
        
        {"role": "user", "content": f"""사용자 질문 : {query}
        RAG 모델 응답 : {response}
        참고 자료: {chunk}
        """}
        ]
        
        # 모델 호출
        result = await clova_model.ainvoke(evaluation_messages)
        evaluation_text = result.content.strip()
        
        # 점수와 평가 이유 추출
        score_match = re.search(r'점수:\s*([01](?:\.\d+)?)', evaluation_text)
        if score_match:
            try:
                score = float(score_match.group(1))
                score = min(max(score, 0.0), 1.0)  # 0~1 범위로 제한
            except ValueError:
                score = 0.4
        else:
            score = 0.4

        # 이유 추출
        reason_match = re.search(r'평가 이유:\s*(.+)', evaluation_text, re.DOTALL)
        if reason_match:
            reason = reason_match.group(1).strip()
        else:
            reason = "평가 이유를 추출할 수 없습니다."

        # 결과 반환
        return {
            "score": score,
            "reason": reason
        }
          
    except Exception as e:
        print(f"평가 중 오류 발생: {e}")
        return {
            "score": 0.4,
            "reason": f"평가 중 오류 발생: {str(e)}"
        }

async def improve_prompt(original_prompt: str) -> str:
    model = await get_clovaX()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
            """당신은 사용자의 질문을 가능한 한 원래 의도에 맞게 개선하는 전문가입니다.
            LLM 모델이 정확한 응답을 제공할 수 있도록, 질문을 최소한으로 다듬어 명확하게 만들어 주세요.

            조건:
            - 원래 질문의 의도를 반드시 유지해야 합니다.
            - 불필요한 변형, 추론 추가, 재작성은 피하세요.
            - 문법, 표현, 모호한 부분만 정리하고, 핵심 내용은 그대로 둡니다.
            - 개선된 질문만 반환하세요.
                """,
            ),
            (
                "human",
                "기존 질문: {original_prompt}\n\n개선된 질문을 작성해주세요:",
            ),
        ]
    )

    # 프롬프트를 구성해서 모델에 전달
    chain = prompt | model
    result = await chain.ainvoke({"original_prompt": original_prompt})

    return result.content