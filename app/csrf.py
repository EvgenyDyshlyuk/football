"""CSRF helpers for server-rendered forms."""

from __future__ import annotations

import hmac
import secrets

from fastapi import HTTPException, Request, Response, status

from app.auth.cookies import SAME_SITE, use_secure_cookies

CSRF_COOKIE = "csrf_token"
CSRF_FIELD = "csrf_token"
CSRF_TOKEN_BYTES = 32


def get_or_create_csrf_token(request: Request) -> str:
    """Return the existing CSRF token cookie or create a new token."""
    token = request.cookies.get(CSRF_COOKIE)
    if token:
        return token
    return secrets.token_urlsafe(CSRF_TOKEN_BYTES)


def set_csrf_cookie(response: Response, request: Request, token: str) -> None:
    """Set the CSRF token cookie with the app's standard cookie attributes."""
    response.set_cookie(
        key=CSRF_COOKIE,
        value=token,
        httponly=True,
        secure=use_secure_cookies(request),
        samesite=SAME_SITE,
    )


def validate_csrf_token(request: Request, submitted_token: str) -> None:
    """Validate a submitted form token against the CSRF cookie."""
    cookie_token = request.cookies.get(CSRF_COOKIE)
    if not cookie_token or not submitted_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

    if not hmac.compare_digest(cookie_token, submitted_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
