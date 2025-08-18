from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.base_response import BaseResponseModel
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat")


@router.get("/run", response_model=BaseResponseModel)
async def chat(name: str, query: str) -> BaseResponseModel:
    status_code, detail = await ChatService.chat_service(name=name, query=query)

    return BaseResponseModel(status_code=status_code, detail=detail)


@router.get("/stream")
async def chat_stream(name: str, query: str, session_id: str):
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        ChatService.chat_stream_service(name=name, query=query, session_id=session_id),
        media_type="text/event-stream",
        headers=headers,
    )
