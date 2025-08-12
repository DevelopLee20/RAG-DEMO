from pydantic import BaseModel


class BaseResponseModel(BaseModel):
    status_code: int
    detail: str
