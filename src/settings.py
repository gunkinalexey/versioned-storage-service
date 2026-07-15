import os

from dotenv import load_dotenv


def string_to_bool(value: str) -> bool:
    return value.lower() in ["true", "1", "t", "y", "yes"]


load_dotenv(override=True)

PUBLIC_API_PREFIX = os.environ.get("PUBLIC_API_PREFIX", "/api/v1")
PUBLIC_API_PORT = int(os.environ.get("PUBLIC_API_PORT", "8000"))
SERVICE_DB_URL = os.environ.get(
    "SERVICE_DB_URL",
    "sqlite+aiosqlite:///./data/storage.db",
)

S3_HOST = os.environ.get("S3_HOST", "localhost")
S3_PORT = os.environ.get("S3_PORT", "9000")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
S3_SECURE = string_to_bool(os.environ.get("S3_SECURE", "False"))
S3_VERIFY_CERTIFICATES = string_to_bool(
    os.environ.get("S3_VERIFY_CERTIFICATES", "False")
)
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
S3_BUCKET = os.environ.get("S3_BUCKET", "versioned-storage")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
NUMBER_OF_WORKERS = int(os.environ.get("NUMBER_OF_WORKERS", "1"))
