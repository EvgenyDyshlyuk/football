"""Configuration loader for AWS Cognito settings."""

import os
from urllib.parse import quote_plus

COGNITO_AUTH_URL_BASE = os.getenv(
    "COGNITO_AUTH_URL_BASE",
    "https://example.auth.eu-west-2.amazoncognito.com/login",
)
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
if not COGNITO_CLIENT_ID:
    raise RuntimeError("Missing COGNITO_CLIENT_ID environment variable")
COGNITO_SCOPE = os.getenv("COGNITO_SCOPE", "email+openid+phone")
COGNITO_REDIRECT_URI = os.getenv("COGNITO_REDIRECT_URI", "http://localhost:8000/")

COGNITO_AUTH_URL = (
    f"{COGNITO_AUTH_URL_BASE}?client_id={COGNITO_CLIENT_ID}&response_type=code&"
    f"scope={COGNITO_SCOPE}&redirect_uri={quote_plus(COGNITO_REDIRECT_URI)}"
)
