"""HTTP route handlers for authentication endpoints."""

from typing import Union

import logging
from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import RedirectResponse, Response as FastAPIResponse

from app.jinja2_env import templates
from app.auth.cognito import authenticate_user

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/login")
async def get_login(request: Request) -> FastAPIResponse:
    """Render the login form."""
    logger.debug("Rendering login form; existing cookies: %r", dict(request.cookies))
    return templates.TemplateResponse(request, "auth/login.html")


@auth_router.post("/login")
async def post_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
) -> Union[FastAPIResponse, Response]:
    """Process the login form submission."""
    auth = authenticate_user(username, password)
    if not auth:
        return Response(
            content='<p class="text-red-500">Invalid credentials</p>',
            media_type="text/html",
        )
    logger.debug("Authentication success for %s", username)
    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key="access_token",
        value=auth["IdToken"],
        httponly=True,
        secure=(request.url.scheme == "https"),
    )
    logger.debug(
        "Setting login access_token cookie, secure=%s", request.url.scheme == "https"
    )
    return redirect
