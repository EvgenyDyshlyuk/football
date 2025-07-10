"""Middleware for automatic token refresh using Cognito."""

from __future__ import annotations

import logging
import time
from typing import Callable, Awaitable

from fastapi import Request, Response
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from .cognito import refresh_access_token

logger = logging.getLogger(__name__)


class RefreshTokenMiddleware(BaseHTTPMiddleware):
    """Refresh the access token on each request if needed."""

    def __init__(self, app, max_age: int = 30 * 24 * 60 * 60) -> None:
        super().__init__(app)
        self.max_age = max_age

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")
        new_access: str | None = None

        if token:
            try:
                claims = jwt.get_unverified_claims(token)
                exp = int(claims.get("exp", 0))
                if exp <= int(time.time()) and refresh_token:
                    tokens = refresh_access_token(refresh_token)
                    new_access = tokens.get("access_token")
                    if new_access:
                        token = new_access
            except JWTError:
                logger.error("Failed to parse JWT for refresh check")
            except Exception:
                logger.exception("Error refreshing token")

        response = await call_next(request)
        new_access = getattr(request.state, "new_access_token", new_access)
        if new_access:
            secure = request.url.scheme == "https"
            response.set_cookie(
                "access_token",
                new_access,
                httponly=True,
                secure=secure,
            )
        return response

