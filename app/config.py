"""Central configuration and environment loading for the app."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Automatically load a local .env file when running in development.
if os.getenv("STAGE", "local") == "local":
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Basic AWS/Cognito settings
COGNITO_REGION = os.getenv("COGNITO_REGION") or os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_APP_CLIENT_SECRET = os.getenv("COGNITO_APP_CLIENT_SECRET")

# OAuth related values
COGNITO_AUTH_URL_BASE = os.getenv("COGNITO_AUTH_URL_BASE")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
COGNITO_SCOPE = os.getenv("COGNITO_SCOPE")
COGNITO_REDIRECT_URI = os.getenv("COGNITO_REDIRECT_URI")

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
if _missing:
    raise RuntimeError(f"Missing environment variables: {', '.join(_missing)}")

# Construct the login URL for the Cognito Hosted UI
_encoded_redirect = quote_plus(COGNITO_REDIRECT_URI, safe="/")
COGNITO_AUTH_URL = (
    f"{COGNITO_AUTH_URL_BASE}?client_id={COGNITO_CLIENT_ID}&response_type=code"
    f"&scope={COGNITO_SCOPE}&redirect_uri={_encoded_redirect}"
)
