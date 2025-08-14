import os

from dotenv import load_dotenv

load_dotenv()

CLOVASTUDIO_API_TOKEN = os.environ.get("CLOVASTUDIO_API_TOKEN")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")
# 강제로 클라우드 서버 사용
LANGFUSE_HOST = "http://192.168.123.60:3000"
LANGFUSE_PROJECT_ID = os.environ.get("LANGFUSE_PROJECT_ID", "cmeatzdr0000rqdrvis6h7k3t")
LANGFUSE_ORG_ID = os.environ.get("LANGFUSE_ORG_ID", "cmeatz45p000mqdrv0f3ewynd")
