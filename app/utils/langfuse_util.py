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
