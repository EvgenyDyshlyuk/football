import os
from pathlib import Path
from dotenv import load_dotenv

if os.getenv("STAGE", "local") == "local":
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

STAGE = os.getenv("STAGE", "local")
COGNITO_REGION = os.getenv("COGNITO_REGION") or os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_APP_CLIENT_SECRET = os.getenv("COGNITO_APP_CLIENT_SECRET")

if not COGNITO_REGION or not COGNITO_USER_POOL_ID:
    raise RuntimeError(
        f"Missing COGNITO_REGION={COGNITO_REGION!r} or COGNITO_USER_POOL_ID={COGNITO_USER_POOL_ID!r}"
    )
