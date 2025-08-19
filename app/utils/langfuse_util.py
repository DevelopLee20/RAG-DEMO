from langfuse.callback import CallbackHandler

from app.core.env import LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY


class LangfuseUtil:
    langfuse_handler = None

    @classmethod
    async def get_langfuse_handler(cls, tags: list[str] = None) -> CallbackHandler:
        """랭퓨즈 클라이언트 반환 함수

        Returns:
            CallbackHandler: 랭퓨즈 클라이언트 객체
        """
        if cls.langfuse_handler is None:
            cls.langfuse_handler = CallbackHandler(
                public_key=LANGFUSE_PUBLIC_KEY,
                secret_key=LANGFUSE_SECRET_KEY,
                host=LANGFUSE_HOST,
                tags=tags,
            )

        return cls.langfuse_handler

    @classmethod
    async def set_langfuse_score(
        cls, value: float, comment: str, name: str = "evalating score"
    ) -> None:
        langfuse_handler = await cls.get_langfuse_handler()

        langfuse_handler.langfuse.score(
            name=name,
            value=value,
            comment=comment,
        )
        langfuse_handler.langfuse.flush()
