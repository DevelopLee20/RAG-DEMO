from fastapi import APIRouter, UploadFile

from app.core.base_response import BaseResponseModel
from app.services import file_service

router = APIRouter(prefix="")


@router.post("/upload", response_model=BaseResponseModel)
async def upload_file(file: UploadFile) -> BaseResponseModel:
    status_code, detail = await file_service.file_upload_service(file=file)

    return BaseResponseModel(status_code=status_code, detail=detail)
