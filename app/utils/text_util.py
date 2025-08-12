import re


def preprocessing_text(text: str) -> str:
    """텍스트 전처리 함수

    Args:
        text (str): 전처리할 텍스트

    Returns:
        str: 전처리된 텍스트
    """
    text = re.sub(r"[^ㄱ-ㅎㅏ-ㅣ가-힣a-zA-Z0-9()+\-*/=<>%., ]", "", text)
    text = re.sub(r" {2,}", " ", text)

    return text
