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

            sys_prompt = """당신은 LLM 모델의 답변을 평가하는 공정하고 엄격한 평가자입니다.
            당신의 임무는 주어진 [질문], [컨텍스트] 그리고 [LLM 답변]을 바탕으로 LLM 모델의 성능을 평가하는 것입니다.
            만약 문서에 없는 질문에 대해 '문서에 없음'이라고 답변했다면, 아주 정확한 답변으로 평가합니다.

            다음 평가 기준에 따라 답변을 분석하고 점수를 매겨주세요:

            평가 결과는 JSON 형식으로 제공해야 합니다. JSON 객체는 다음 키를 포함해야 합니다:
            -   `score`: (정수, 0.0000-1.0000) 전반적인 답변 품질에 대한 점수. 1.0000은 완벽한 답변, 0.0000은 매우 나쁜 답변을 의미합니다.
            -   `reason`: (문자열) 각 평가 기준에 대한 분석과 점수에 대한 이유를 20자 이내 한 줄로 설명합니다.
            
            {format_instructions}
            """

            user_prompt = """[질문]
            {question}

            [컨텍스트]
            {context}

            [LLM 답변]
            {llm_answer}
            """

            prompt_template = ChatPromptTemplate.from_messages(
                messages=[("system", sys_prompt), ("human", user_prompt)]
            ).partial(format_instructions=parser.get_format_instructions())

            llm_model = await cls.get_clovaX()
            # 프롬프트, 모델, 파서를 연결하고 전역 변수에 할당하여 캐싱
            cls.evalate_chain_clovaX = prompt_template | llm_model | parser

        return cls.evalate_chain_clovaX
