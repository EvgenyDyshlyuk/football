"""Authentication dependencies used across the application."""

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt

if os.getenv("STAGE") == "local" or not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_REGION = os.getenv("COGNITO_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
USER_POOL_ID = COGNITO_USER_POOL_ID
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

jwks_url = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()

security = HTTPBearer()


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Validate the Cognito JWT from Authorization header or cookie.

    Returns the decoded JWT payload or raises ``HTTPException`` if the
    token is invalid or expired.
    """
    credentials = token.credentials
    try:
        header = jwt.get_unverified_header(credentials)
        key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])
        public_key = jwk.construct(key)
        payload = jwt.decode(
            credentials,
            public_key,
            algorithms=[key["alg"]],
            audience=CLIENT_ID,
        )
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
