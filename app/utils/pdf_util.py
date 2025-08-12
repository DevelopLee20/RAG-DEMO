from typing import Any

import PyPDF2
from fastapi import UploadFile

from app.utils.text_util import preprocessing_text


async def parse_pdf(file: str | UploadFile) -> list[str]:
    """pdf 파일 또는 UploadFile 스트림을 받아서 파싱 리스트 반환

    Args:
        file (str): 파일명 또는 파일 스트림 객체

    Returns:
        list[str]: 파싱 리스트 반환
    """
    parse_list = []

    pdf: Any
    # file의 타입에 따라 형식 변경
    if isinstance(file, str):
        pdf = file
    else:
        pdf = file.file

    for page in PyPDF2.PdfReader(pdf).pages:
        text = page.extract_text()
        processed_text = preprocessing_text(text=text)

        parse_list.append(processed_text)

    return parse_list
