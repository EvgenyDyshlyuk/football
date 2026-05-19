"""HTTP route handlers for authentication endpoints."""

import logging
from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse, Response as FastAPIResponse

from app.auth.cookies import delete_auth_cookies
from app.config import (
    COGNITO_APP_CLIENT_ID,
    COGNITO_AUTH_URL,
    COGNITO_AUTH_URL_BASE,
    COGNITO_REDIRECT_URI,
    LOCAL_AUTH_ENABLED,
)

if not COGNITO_AUTH_URL_BASE and not LOCAL_AUTH_ENABLED:  # to ensure str
    raise ValueError("COGNITO_AUTH_URL_BASE must be set in the configuration")

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/login")
async def get_login(request: Request) -> FastAPIResponse:
    """Redirect directly to Cognito's hosted UI."""
    if LOCAL_AUTH_ENABLED:
        return RedirectResponse(url="/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    logger.debug("Redirecting to Cognito login")
    return RedirectResponse(url=COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.get("/logout")
async def logout(request: Request) -> FastAPIResponse:
    """Clear session cookies and optionally redirect to Cognito."""
    if LOCAL_AUTH_ENABLED:
        return RedirectResponse(url="/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    logout_url = COGNITO_AUTH_URL_BASE.replace("/login", "/logout")
    logout_url += f"?client_id={COGNITO_APP_CLIENT_ID}&logout_uri={COGNITO_REDIRECT_URI}"
    resp = RedirectResponse(url=logout_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    delete_auth_cookies(resp, request)
    logger.debug("User logged out, cookies cleared")
    return resp
