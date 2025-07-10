"""HTTP route handlers for authentication endpoints."""

import logging
from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse, Response as FastAPIResponse

from app.config import COGNITO_AUTH_URL, COGNITO_AUTH_URL_BASE, COGNITO_CLIENT_ID, COGNITO_REDIRECT_URI

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/login")
async def get_login(request: Request) -> FastAPIResponse:
    """Redirect directly to Cognito's hosted UI."""
    logger.debug("Redirecting to Cognito login; existing cookies: %r", dict(request.cookies))
    return RedirectResponse(url=COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.get("/logout")
async def logout(request: Request) -> FastAPIResponse:
    """Clear session cookies and optionally redirect to Cognito."""
    logout_url = COGNITO_AUTH_URL_BASE.replace("/login", "/logout")
    logout_url += f"?client_id={COGNITO_CLIENT_ID}&logout_uri={COGNITO_REDIRECT_URI}"
    resp = RedirectResponse(url=logout_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    secure_flag = request.url.scheme == "https"
    resp.delete_cookie("access_token", httponly=True, secure=secure_flag)
    resp.delete_cookie("refresh_token", httponly=True, secure=secure_flag)
    logger.debug("User logged out, cookies cleared")
    return resp
