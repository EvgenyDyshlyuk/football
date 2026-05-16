"""Authentication dependencies used across the application."""

import logging
from typing import Any, Dict

import requests
from functools import lru_cache
from requests.exceptions import RequestException
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from app.auth.cognito import fetch_user_attributes, refresh_access_token
from app.config import (
    COGNITO_APP_CLIENT_ID,
    COGNITO_REGION,
    COGNITO_USER_POOL_ID,
    LOCAL_AUTH_EMAIL,
    LOCAL_AUTH_ENABLED,
    LOCAL_AUTH_NICKNAME,
    LOCAL_AUTH_SUB,
    LOCAL_AUTH_USERNAME,
)

logger = logging.getLogger(__name__)

CLIENT_ID = COGNITO_APP_CLIENT_ID

# Build and log the JWKS URL
jwks_url = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"
    f"{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)
logger.debug("JWKS URL → %s", jwks_url)


@lru_cache
def get_jwks() -> Dict[str, Any]:
    """Fetch and cache the Cognito JWKS document."""
    try:
        resp = requests.get(jwks_url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except (RequestException, ValueError) as exc:
        logger.error("Failed to fetch JWKS: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to load JWKS",
        )


security = HTTPBearer(auto_error=False)


def get_local_user() -> Dict[str, Any]:
    """Return the configured local development user."""
    return {
        "sub": LOCAL_AUTH_SUB,
        "username": LOCAL_AUTH_USERNAME,
        "email": LOCAL_AUTH_EMAIL,
        "attributes": {
            "email": LOCAL_AUTH_EMAIL,
            "nickname": LOCAL_AUTH_NICKNAME,
        },
    }


def get_current_user(
    request: Request,
    token: HTTPAuthorizationCredentials | None = Depends(security),
) -> Dict[str, Any]:
    """Validate the Cognito JWT from the Authorization header or cookie.

    Returns the decoded JWT payload with user attributes, or raises HTTPException.
    """
    if LOCAL_AUTH_ENABLED:
        return get_local_user()

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

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
        key = next(k for k in get_jwks().get("keys", []) if k.get("kid") == kid)
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
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            try:
                tokens = refresh_access_token(refresh_token)
                new_access = tokens.get("access_token")
                if new_access:
                    request.state.new_access_token = new_access
                    new_creds = HTTPAuthorizationCredentials(
                        scheme="Bearer", credentials=new_access
                    )
                    return get_current_user(request, token=new_creds)
            except Exception:
                logger.exception("Failed automatic refresh")
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

    # 3) Fetch Cognito user attributes if possible
    username = payload.get("username")
    # Ensure username is present
    if not username:
        logger.error("Token payload missing 'username'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        attrs = fetch_user_attributes(username)
    except Exception as exc:
        logger.exception("Failed to fetch user attributes for %s: %s", username, exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to fetch user data",
        )

    payload["attributes"] = attrs
    return payload
