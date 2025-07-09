"""Authentication dependencies used across the application."""

from typing import Any, Dict

import logging
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from app.core.config import (
    COGNITO_REGION,
    COGNITO_USER_POOL_ID,
    COGNITO_APP_CLIENT_ID,
)

CLIENT_ID = COGNITO_APP_CLIENT_ID

jwks_url = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"
    f"{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)

logger = logging.getLogger(__name__)
logger.debug("JWKS URL → %s", jwks_url)

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
    except StopIteration:
        logger.error("JWT kid %s not found in JWKS", header.get("kid"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signing key not found",
        )
    except Exception as exc:
        logger.error("Failed to parse token header: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    try:
        public_key = jwk.construct(key)
        payload = jwt.decode(
            credentials,
            public_key,
            algorithms=[key["alg"]],
            audience=CLIENT_ID,
        )
        return payload
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
    except Exception:
        logger.exception("Unexpected error during JWT validation")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
