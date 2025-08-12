from langchain_core.documents import Document
from langchain_naver import ClovaXEmbeddings
from langchain_community.vectorstores import FAISS

from app.utils.langchain_util import get_embedding

vector_store = None

def create_vector_store(name: str, chunks: list[Document]):
    """FAISS 벡터 데이터베이스 생성

    Args:
        name (str): 데이터베이스 이름
        chunks (list[Document]): 청크(Documents)
        embedding (ClovaXEmbeddings): 임베딩 객체
    """
    if vector_store is None:
        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=get_embedding(),
        )
    
    vector_store.save_local(name)

def select_vector_store(name: str) -> FAISS:
    """벡터 스토어를 불러오는 함수

    Args:
        name (str): 벡터 스토어 이름

    Returns:
        FAISS: 벡터 스토어 객체
    """
    return FAISS.load_local(
        name, 
        get_embedding(),
        allow_dangerous_deserialization=True # pickle 파일 로드 허용
    )