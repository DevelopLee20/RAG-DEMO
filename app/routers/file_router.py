from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.base_response import BaseResponseModel, ListResponseModel
from app.services.file_service import FileService

router = APIRouter(prefix="/file")


@router.post("/upload", response_model=BaseResponseModel)
async def upload_file(file: UploadFile) -> BaseResponseModel:
    status_code, detail = await FileService.file_upload_service(file=file)

    return BaseResponseModel(status_code=status_code, detail=detail)


@router.get("/list", response_model=ListResponseModel)
async def get_pdf_file_list() -> ListResponseModel:
    status_code, detail, data = await FileService.file_list_get_service()

    return ListResponseModel(status_code=status_code, detail=detail, data=data)


@router.get("/{file_name}")
async def get_file(file_name: str):
    file_path = await FileService.file_path_get_service(name=file_name)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@router.delete("/{file_name}")
async def delete_file(file_name: str):
    status_code, detail = await FileService.file_delete_service(name=file_name)
    return BaseResponseModel(status_code=status_code, detail=detail)
