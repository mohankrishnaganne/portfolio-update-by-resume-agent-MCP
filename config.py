import os
from dotenv import load_dotenv

load_dotenv()

def _get_env_or_none(key: str, default: str | None = None) -> str | None:
    """Get environment variable, return None if empty string or not set."""
    value = os.getenv(key, default)
    return value if value else None

# AWS Configuration
AWS_ACCESS_KEY_ID = _get_env_or_none("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = _get_env_or_none("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = _get_env_or_none("S3_BUCKET_NAME")

# AI Configuration
GEMINI_API_KEY = _get_env_or_none("GEMINI_API_KEY")


def get_missing_config() -> list[str]:
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not AWS_ACCESS_KEY_ID:
        missing.append("AWS_ACCESS_KEY_ID")
    if not AWS_SECRET_ACCESS_KEY:
        missing.append("AWS_SECRET_ACCESS_KEY")
    if not S3_BUCKET_NAME:
        missing.append("S3_BUCKET_NAME")
    return missing