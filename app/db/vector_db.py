import os
import shutil

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.utils.langchain_util import get_embedding

vector_store = None


async def create_vector_store(name: str, chunks: list[Document]):
    """FAISS 벡터 데이터베이스 생성

    Args:
        name (str): 데이터베이스 이름
        chunks (list[Document]): 청크(Documents)
        embedding (ClovaXEmbeddings): 임베딩 객체
    """
    global vector_store

    if vector_store is None:
        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=await get_embedding(),
        )

    os.makedirs("./vector_db/", exist_ok=True)
    vector_store.save_local("./vector_db/" + name)


async def select_vector_store(name: str) -> FAISS | None:
    """벡터 스토어를 불러오는 함수

    Args:
        name (str): 벡터 스토어 이름

    Returns:
        FAISS: 벡터 스토어 객체
    """
    try:
        return FAISS.load_local(
            "./vector_db/" + name,
            await get_embedding(),
            allow_dangerous_deserialization=True,  # pickle 파일 로드 허용
        )
    except Exception as e:
        return None


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
