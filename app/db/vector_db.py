import os
import shutil

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.utils.langchain_util import LangchainUtil


class VectorDB:
    # vector_store = None

    @classmethod
    async def create_vector_store(cls, name: str, chunks: list[Document]):
        """FAISS 벡터 데이터베이스 생성

        Args:
            name (str): 데이터베이스 이름
            chunks (list[Document]): 청크(Documents)
            embedding (ClovaXEmbeddings): 임베딩 객체
        """
        os.makedirs("./vector_db/", exist_ok=True)

        vector_store = await cls.select_vector_store(name)
        if vector_store is None:
            vector_store = FAISS.from_documents(
                documents=chunks,
                embedding=await LangchainUtil.get_embedding(),
            ).save_local("./vector_db/" + name)

    @staticmethod
    async def select_vector_store(safe_name: str) -> FAISS | None:
        """벡터 스토어를 불러오는 함수

        Args:
            name (str): 벡터 스토어 이름

        Returns:
            FAISS: 벡터 스토어 객체
        """
        try:
            return FAISS.load_local(
                "./vector_db/" + safe_name,
                await LangchainUtil.get_embedding(),
                allow_dangerous_deserialization=True,  # pickle 파일 로드 허용
            )
        except Exception as e:
            return None

    @staticmethod
    async def delete_vector_store(name: str) -> bool:
        """벡터 스토어를 삭제하는 함수

        Args:
            name (str): 삭제할 벡터 스토어 이름

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            vector_store_path = f"./vector_db/{name}"
            if os.path.exists(vector_store_path):
                shutil.rmtree(vector_store_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting vector store {name}: {e}")
            return False
