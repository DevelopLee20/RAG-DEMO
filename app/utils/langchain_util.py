from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_naver import ChatClovaX, ClovaXEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.base_models import EvaluationModel
from app.core.env import CLOVASTUDIO_API_TOKEN
from app.utils.langfuse_util import LangfuseUtil


class LangchainUtil:
    splitter = None
    embedding = None
    chain_clovaX = None
    evalate_chain_clovaX = None
    clovaX = None
    langfuse_handler = None
    chat_store_dict: dict[str, ChatMessageHistory] = {}  # 채팅 히스토리 저장용

    @classmethod
    async def get_session_history(cls, session_id: str) -> ChatMessageHistory:
        """세션 히스토리를 가져오는 함수

        Args:
            session_id (str): 세션 ID

        Returns:
            ChatMessageHistory: 세션 히스토리 객체
        """
        if session_id not in cls.chat_store_dict:
            cls.chat_store_dict[session_id] = ChatMessageHistory()
        return cls.chat_store_dict[session_id]

    @classmethod
    async def get_splitter(cls) -> RecursiveCharacterTextSplitter:
        """텍스트 파싱 스플리터 객체 반환

        Returns:
            RecursiveCharacterTextSplitter: 스플리터 객체
        """
        if cls.splitter is None:
            cls.splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=20
            )

        return cls.splitter

    @classmethod
    async def create_chunks_to_text(cls, texts: list[str]) -> list[Document]:
        """텍스트를 받아서 청크 리스트를 생성하는 함수

        Args:
            texts (list[str]): 텍스트 리스트

        Returns:
            list[Document]: 청크 리스트 객체
        """
        splitter = await cls.get_splitter()

        return splitter.create_documents(texts=texts)

    @classmethod
    async def get_embedding(cls) -> ClovaXEmbeddings:
        """임베딩을 반환하는 함수

        Returns:
            ClovaXEmbeddings: 생성된 임베딩
        """

        if cls.embedding is None:
            cls.embedding = ClovaXEmbeddings(
                model="bge-m3",
                dimensions=1024,
                api_key=CLOVASTUDIO_API_TOKEN,
            )

        return cls.embedding

    @classmethod
    async def get_clovaX(cls) -> ChatClovaX:
        """클로바엑스 객체 반환 함수

        Returns:
            ChatClovaX: 클로바엑스 객체
        """
        if cls.clovaX is None:
            cls.clovaX = ChatClovaX(
                model="HCX-003",
                max_tokens=128,
                api_key=CLOVASTUDIO_API_TOKEN,
            )

        return cls.clovaX

    @classmethod
    async def get_chain_clovaX(cls):
        """클로바엑스 프롬프트 체인 객체 반환 함수

        Returns:
            Chain: 모델과 프롬프트 체인 객체
        """
        if cls.chain_clovaX is None:
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

            clova_model = await cls.get_clovaX()
            cls.chain_clovaX = prompt | clova_model

        return cls.chain_clovaX

    @classmethod
    async def use_chain_clovaX(cls, chunk: list[Document], query: str) -> str:
        """체이닝된 클로바엑스 객체 사용 함수

        Args:
            chunk (list[Document]): 가장 유사도 높은 청크
            query (str): 질문

        Returns:
            str: 질문에 대한 대답
        """
        chain = await cls.get_chain_clovaX()
        langfuse_handler = await LangfuseUtil.get_langfuse_handler()

        result = await chain.ainvoke(
            {
                "results": chunk,
                "query": query,
            },
            config={"callbacks": [langfuse_handler]},
        )
        return result.content

    @classmethod
    async def add_to_history(cls, session_id: str, query: str, response: str) -> None:
        """세션 히스토리에 대화 내용을 추가하는 함수

        Args:
            session_id (str): 세션 ID
            query (str): 사용자 질문
            response (str): AI 응답
        """
        history: ChatMessageHistory = cls.get_session_history(session_id)
        history.add_user_message(query)
        history.add_ai_message(response)

    @classmethod
    async def evalate_llm_score(
        cls, query: str, answer: str, context: str = None
    ) -> None:
        """LLM의 답변을 평가하고 그 결과를 Langfuse에 기록합니다."""
        try:
            # 체이닝된 LLM 모델 불러오기
            chaining_model = await cls.get_evalate_chaining_model()
            # 모델을 호출하여 JSON 형식의 평가 결과를 직접 받음
            json_result = await chaining_model.ainvoke(
                {
                    "question": query,
                    "llm_answer": answer,
                    "context": context or "제공된 컨텍스트 없음",
                },
            )

            langfuse_handler = await LangfuseUtil.get_langfuse_handler()

            langfuse_handler.langfuse.score(
                name="eval score",
                value=float(json_result["score"]),
                comment=json_result["reason"],
            )

            langfuse_handler.langfuse.flush()
        except Exception as e:
            print(f"LLM 답변 평가 중 오류 발생: {e}")

    @classmethod
    async def get_evalate_chaining_model(cls):

        if cls.evalate_chain_clovaX is None:
            # Pydantic 모델을 기반으로 JSON 출력 파서 생성
            parser = JsonOutputParser(pydantic_object=EvaluationModel)

            sys_prompt = """당신은 RAG 모델의 응답 정확도를 평가하는 전문가입니다.

            다음 정보를 바탕으로 모델의 응답이 검색된 참고 문서의 내용에 얼마나 정확히 기반했는지 평가하세요:

            - 사용자 질문: {question}
            - RAG 모델의 응답: {llm_answer}
            - 참고 문서: {context}

            다음 기준을 따라 평가하세요:

            1. 질문에 대한 **정확한 정보가 문서에 포함되어 있는 경우**, 모델 응답이 해당 정보를 **정확히 반영하고 왜곡 없이 요약 또는 인용했는지** 평가하세요.

            2. 질문에 대한 정보가 **문서에 존재하지 않는 경우**, 아래 두 가지 중 하나면 정확한 응답으로 간주하고 **정확도 점수 1.00**을 부여하세요:
            - 모델이 "문서에 없음" 또는 이와 동등한 표현으로 답한 경우
            - 모델이 **응답하지 않았으며**, 이는 문서에 정보가 없기 때문이라고 판단되는 경우

            3. 반대로, 문서에 정보가 없음에도 불구하고 모델이 **추측으로 답변한 경우**, 정확도 점수는 낮아야 합니다 (예: 0.0 ~ 0.3).
            
            출력
            - 출력은 항상 json 형식으로 반환해주세요.
            - 'score': 0.00~1.00 사이의 정확도 점수
            - 'reason' : 점수를 부여한 이유. 짧게 15자 이내 서술
            """

            user_prompt = """[사용자 질문]
            {question}

            [참고 문서]
            {context}

            [RAG 모델의 응답]
            {llm_answer}
            """

            prompt_template = ChatPromptTemplate.from_messages(
                messages=[("system", sys_prompt), ("human", user_prompt)]
            ).partial(format_instructions=parser.get_format_instructions())

            llm_model = await cls.get_clovaX()
            # 프롬프트, 모델, 파서를 연결하고 전역 변수에 할당하여 캐싱
            cls.evalate_chain_clovaX = prompt_template | llm_model | parser

        return cls.evalate_chain_clovaX
