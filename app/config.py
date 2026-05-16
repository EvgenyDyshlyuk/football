"""Central configuration and environment loading for the app."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

STAGE = os.getenv("STAGE", "local")

# Automatically load a local .env file when running in development.
if STAGE == "local":
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _is_enabled(value: str | None) -> bool:
    return value is not None and value.lower() in {"1", "true", "yes", "on"}


# Local-only test user for development without a real Cognito login.
LOCAL_AUTH_ENABLED = STAGE == "local" and _is_enabled(os.getenv("LOCAL_AUTH_ENABLED"))
LOCAL_AUTH_SUB = os.getenv("LOCAL_AUTH_SUB", "local-test-user")
LOCAL_AUTH_EMAIL = os.getenv("LOCAL_AUTH_EMAIL", "test-codex@example.com")
LOCAL_AUTH_USERNAME = os.getenv("LOCAL_AUTH_USERNAME", LOCAL_AUTH_EMAIL)
LOCAL_AUTH_NICKNAME = os.getenv("LOCAL_AUTH_NICKNAME", "Codex Test")

# Basic AWS/Cognito settings
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
COGNITO_REGION = os.getenv("COGNITO_REGION") or os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_APP_CLIENT_SECRET = os.getenv("COGNITO_APP_CLIENT_SECRET")

# OAuth related values
COGNITO_AUTH_URL_BASE = os.getenv("COGNITO_AUTH_URL_BASE")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
COGNITO_SCOPE = os.getenv("COGNITO_SCOPE")
COGNITO_REDIRECT_URI = os.getenv("COGNITO_REDIRECT_URI")

# DynamoDB tables
MATCHES_TABLE_NAME = os.getenv("MATCHES_TABLE_NAME")
MATCHES_USE_MEMORY = STAGE == "local" and _is_enabled(os.getenv("MATCHES_USE_MEMORY"))

_missing = [
    name
    for name, val in [
        ("COGNITO_REGION", COGNITO_REGION),
        ("COGNITO_USER_POOL_ID", COGNITO_USER_POOL_ID),
        ("COGNITO_APP_CLIENT_ID", COGNITO_APP_CLIENT_ID),
        ("COGNITO_AUTH_URL_BASE", COGNITO_AUTH_URL_BASE),
        ("COGNITO_CLIENT_ID", COGNITO_CLIENT_ID),
        ("COGNITO_SCOPE", COGNITO_SCOPE),
        ("COGNITO_REDIRECT_URI", COGNITO_REDIRECT_URI),
    ]
    if not val
]
if _missing and not LOCAL_AUTH_ENABLED:
    raise RuntimeError(f"Missing environment variables: {', '.join(_missing)}")

if STAGE != "local" and not MATCHES_TABLE_NAME:
    raise RuntimeError("MATCHES_TABLE_NAME must be set outside local development")

# Separatly ensure the redirect URI is properly encoded for URL usage to make pylance happy
if not COGNITO_REDIRECT_URI and not LOCAL_AUTH_ENABLED:
    raise RuntimeError("COGNITO_REDIRECT_URI must be set in environment variables")

# Construct the login URL for the Cognito Hosted UI
if COGNITO_AUTH_URL_BASE and COGNITO_CLIENT_ID and COGNITO_SCOPE and COGNITO_REDIRECT_URI:
    _encoded_redirect = quote_plus(COGNITO_REDIRECT_URI, safe="/")
    COGNITO_AUTH_URL = (
        f"{COGNITO_AUTH_URL_BASE}?client_id={COGNITO_CLIENT_ID}&response_type=code"
        f"&scope={COGNITO_SCOPE}&redirect_uri={_encoded_redirect}"
    )
else:
    COGNITO_AUTH_URL = "/"
