from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_naver import ClovaXEmbeddings

from app.core.env import CLOVASTUDIO_API_TOKEN

splitter = None
embedding = None

def get_splitter() -> RecursiveCharacterTextSplitter:
    """텍스트 파싱 스플리터 객체 반환

    Returns:
        RecursiveCharacterTextSplitter: 스플리터 객체
    """
    if splitter is None:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=20
        )
    
    return splitter

def get_chunks_to_text(texts: list[str]) -> list[Document]:
    """텍스트를 받아서 청크 리스트를 반환하는 함수

    Args:
        texts (list[str]): 텍스트 리스트

    Returns:
        list[Document]: 청크 리스트 객체
    """
    return get_splitter().create_documents(texts=texts)

def get_embedding() -> ClovaXEmbeddings:
    if embedding is None:
        embedding = ClovaXEmbeddings(
        model="bge-m3",
        dimensions=1024,
        api_key=CLOVASTUDIO_API_TOKEN,
    )
    
    return embedding
