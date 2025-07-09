"""HTTP route handlers for authentication endpoints."""

import logging
from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse, Response as FastAPIResponse

from app.config import COGNITO_AUTH_URL

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/login")
async def get_login(request: Request) -> FastAPIResponse:
    """Redirect directly to Cognito's hosted UI."""
    logger.debug("Redirecting to Cognito login; existing cookies: %r", dict(request.cookies))
    return RedirectResponse(url=COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


