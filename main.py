import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.file_router import router as f_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=f_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"I'm ready": "OK"}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
