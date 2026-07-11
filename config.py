import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_PAT = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

if not GEMINI_API_KEY or not GITHUB_PAT:
    raise ValueError("Missing required environment variables. Check your .env file.")