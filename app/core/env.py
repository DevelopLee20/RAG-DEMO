import os

from dotenv import load_dotenv

load_dotenv()

CLOVASTUDIO_API_TOKEN = os.environ.get("CLOVASTUDIO_API_TOKEN")
