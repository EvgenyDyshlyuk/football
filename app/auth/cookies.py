"""Cookie helpers for authentication tokens."""

from fastapi import Request, Response

from app.config import STAGE

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_TOKEN_MAX_AGE = 30 * 24 * 60 * 60
SAME_SITE = "lax"


def use_secure_cookies(request: Request) -> bool:
    """Return whether auth cookies should be marked Secure for this request."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    forwarded_scheme = forwarded_proto.split(",", 1)[0].strip().lower()
    return STAGE != "local" or forwarded_scheme == "https" or request.url.scheme == "https"


def set_access_token_cookie(response: Response, request: Request, token: str) -> None:
    """Set the access token cookie with consistent security attributes."""
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=use_secure_cookies(request),
        samesite=SAME_SITE,
    )


def set_refresh_token_cookie(response: Response, request: Request, token: str) -> None:
    """Set the refresh token cookie with consistent security attributes."""
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=use_secure_cookies(request),
        samesite=SAME_SITE,
        max_age=REFRESH_TOKEN_MAX_AGE,
    )


def delete_auth_cookies(response: Response, request: Request) -> None:
    """Delete auth cookies with matching security attributes."""
    secure = use_secure_cookies(request)
    response.delete_cookie(
        ACCESS_TOKEN_COOKIE,
        httponly=True,
        secure=secure,
        samesite=SAME_SITE,
    )
    response.delete_cookie(
        REFRESH_TOKEN_COOKIE,
        httponly=True,
        secure=secure,
        samesite=SAME_SITE,
    )
