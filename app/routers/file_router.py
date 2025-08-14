from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

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


@router.get("/files/{file_name}")
async def get_file(file_name: str):
    file_path = await file_service.get_file_path_service(name=file_name)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@router.delete("/files/{file_name}")
async def delete_file(file_name: str):
    status_code, detail = await file_service.file_delete_service(name=file_name)
    return BaseResponseModel(status_code=status_code, detail=detail)

@router.get("/stream")
async def chat_stream(name: str, query: str, session_id: str):
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        file_service.chat_stream_service(name=name, query=query, session_id=session_id),
        media_type="text/event-stream",
        headers=headers,
    )
