from fastapi import APIRouter, UploadFile

from fastapi.responses import StreamingResponse

from app.core.base_response import BaseResponseModel, ListResponseModel
from app.services import file_service

router = APIRouter(prefix="")


@router.post("/upload", response_model=BaseResponseModel)
async def upload_file(file: UploadFile) -> BaseResponseModel:
    status_code, detail = await file_service.file_upload_service(file=file)

    return BaseResponseModel(status_code=status_code, detail=detail)


@router.get("/chat", response_model=BaseResponseModel)
async def chat(name: str, query: str) -> BaseResponseModel:
    status_code, detail = await file_service.chat_service(name=name, query=query)

    return BaseResponseModel(status_code=status_code, detail=detail)


@router.get("/list", response_model=ListResponseModel)
async def get_pdf_file_list() -> ListResponseModel:
    status_code, detail, data = await file_service.get_pdf_file_list()

    return ListResponseModel(status_code=status_code, detail=detail, data=data)


@router.get("/stream")
async def chat_stream(name : str, query :str):
    return StreamingResponse(
        file_service.chat_stream_service(name = name, query = query), 
        media_type = "text/event-stream"
    )