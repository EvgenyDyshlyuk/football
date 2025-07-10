"""Authentication dependencies used across the application."""

import logging
from typing import Any, Dict

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from app.auth.cognito import fetch_user_attributes
from app.core.config import COGNITO_REGION, COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID

logger = logging.getLogger(__name__)

CLIENT_ID = COGNITO_APP_CLIENT_ID

# Build and log the JWKS URL
jwks_url = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"
    f"{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)
logger.debug("JWKS URL → %s", jwks_url)

# Fetch JWKS once at import time
jwks = requests.get(jwks_url).json()

security = HTTPBearer()


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Validate the Cognito JWT from the Authorization header or cookie.

    Returns the decoded JWT payload with user attributes, or raises HTTPException.
    """
    credentials = token.credentials
    header: Dict[str, Any] = {}

    # 1) Parse and locate the correct signing key
    try:
        header = jwt.get_unverified_header(credentials)
    except JWTError as exc:
        logger.error("Failed to parse token header: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    kid = header.get("kid")
    if not isinstance(kid, str):
        logger.error("Token header missing 'kid'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    try:
        key = next(k for k in jwks.get("keys", []) if k.get("kid") == kid)
    except StopIteration:
        logger.error("JWT kid %s not found in JWKS", kid)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signing key not found",
        )

    # 2) Validate and decode the token
    try:
        public_key = jwk.construct(key)
        payload = jwt.decode(
            credentials,
            public_key,
            algorithms=[key.get("alg", "")],
            audience=CLIENT_ID,
        )
    except ExpiredSignatureError as exc:
        logger.error("Token expired: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTError as exc:
        logger.error("JWT error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as exc:
        logger.exception("Unexpected error during JWT validation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # 3) Fetch Cognito user attributes
    username = payload.get("username")
    if not isinstance(username, str):
        logger.error("JWT payload missing or invalid 'username' claim: %r", payload.get("username"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        attrs = fetch_user_attributes(username)
    except Exception as exc:
        logger.exception("Failed to fetch user attributes for %s: %s", username, exc)
        # Depending on your policy, you might reject here or continue without attrs
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to fetch user data",
        )

    payload["attributes"] = attrs
    return payload
