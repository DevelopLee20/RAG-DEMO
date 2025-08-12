from langchain_core.documents import Document
from langchain_naver import ClovaXEmbeddings
from langchain_community.vectorstores import FAISS

vector_store = None

def create_vector_store(name: str, chunks: list[Document], embedding: ClovaXEmbeddings):
    """FAISS 벡터 데이터베이스 생성

    Args:
        name (str): 데이터베이스 이름
        chunks (list[Document]): 청크(Documents)
        embedding (ClovaXEmbeddings): 임베딩 객체
    """
    if vector_store is None:
        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=embedding,
        )
    
    vector_store.save_local(name)
