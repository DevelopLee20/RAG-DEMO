import os

from dotenv import load_dotenv

load_dotenv()

CLOVASTUDIO_API_TOKEN = os.environ.get("CLOVASTUDIO_API_TOKEN")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST")
