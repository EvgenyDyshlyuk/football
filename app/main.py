"""Application entry point for the FastAPI application."""

from pathlib import Path

import logging
import os
from typing import Any, Dict

import requests
from app.logger import configure_logging
from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPAuthorizationCredentials
from app.auth import dependencies as auth_dependencies
from app.auth.cookies import (
    ACCESS_TOKEN_COOKIE,
    set_access_token_cookie,
    set_refresh_token_cookie,
)
from app.auth.dependencies import get_current_user
from app.auth.routes import auth_router
from app.config import COGNITO_AUTH_URL
from app.csrf import get_or_create_csrf_token, set_csrf_cookie, validate_csrf_token
from app.jinja2_env import templates
from app.auth.cognito import exchange_code_for_tokens
from app.auth.middleware import RefreshTokenMiddleware

configure_logging()

logger = logging.getLogger(__name__)

# API Gateway configuration
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
API_GATEWAY_ID = os.getenv("API_GATEWAY_ID")

def _api_base() -> str:
    if not API_GATEWAY_ID:
        raise RuntimeError("API_GATEWAY_ID environment variable is not set")
    return f"https://{API_GATEWAY_ID}.execute-api.{AWS_REGION}.amazonaws.com"

def fetch_user_settings(sub: str) -> Dict[str, Any]:
    url = f"{_api_base()}/user/{sub}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()
    return resp.json()

def save_user_settings(sub: str, nickname: str, preferred_class: str) -> None:
    url = f"{_api_base()}/user/{sub}"
    payload = {"nickname": nickname, "preferred_class": preferred_class}
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()

# Determine this file’s parent dir (i.e. the "app/" folder)
BASE_DIR = Path(__file__).parent

app = FastAPI()
app.add_middleware(RefreshTokenMiddleware)

# Mount the static directory under /static, using the app/static folder
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

# Include your Cognito-based auth routes at /auth
app.include_router(auth_router)


@app.get("/", include_in_schema=False)
async def root(request: Request) -> Response:
    """Render the homepage if the user has a valid token, otherwise redirect."""

    auth_header = request.headers.get("Authorization")
    cookie_token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    code = request.query_params.get("code")

    logger.debug(
        "Auth request received: has_authorization=%s has_access_cookie=%s has_code=%s",
        bool(auth_header),
        bool(cookie_token),
        bool(code),
    )

    if auth_dependencies.LOCAL_AUTH_ENABLED:
        return templates.TemplateResponse(
            request,
            "home.html",
            {"user": auth_dependencies.get_local_user()},
        )

    # If Cognito redirected back with a code, exchange and set cookie
    if code:
        tokens = exchange_code_for_tokens(code)
        access_token = tokens.get("access_token") or tokens.get("id_token")
        refresh_token = tokens.get("refresh_token")
        if not access_token:
            raise RuntimeError("Cognito did not return an access or ID token")

        redirect = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
        set_access_token_cookie(redirect, request, access_token)
        if refresh_token:
            set_refresh_token_cookie(redirect, request, refresh_token)
        logger.debug("Cognito callback exchanged code and set auth cookies")
        return redirect

    # If we have credentials in header or cookie, validate and show home
    if auth_header or cookie_token:
        scheme = "Bearer"
        token = cookie_token or ""
        if auth_header:
            scheme, _, token = auth_header.partition(" ")

        user = None
        if token:
            creds = HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
            try:
                user = auth_dependencies.get_current_user(request=request, token=creds)
            except TypeError:
                user = auth_dependencies.get_current_user(token=creds)
            except Exception:
                return RedirectResponse(
                    COGNITO_AUTH_URL,
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                )

        logger.debug("Authenticated homepage request for sub=%s", user.get("sub") if user else None)
        # TemplateResponse now expects the request first
        return templates.TemplateResponse(request, "home.html", {"user": user})

    # No code, no creds → start login
    return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/settings", include_in_schema=False)
async def get_settings(request: Request, user: Dict[str, Any] = Depends(get_current_user)) -> Response:
    """Render the user settings form populated from API Gateway."""
    settings = {
        "nickname": user.get("attributes", {}).get("nickname", ""),
        "preferred_class": "",
    } if auth_dependencies.LOCAL_AUTH_ENABLED else {}

    try:
        if not auth_dependencies.LOCAL_AUTH_ENABLED:
            settings = fetch_user_settings(user["sub"])
    except Exception:
        logger.exception("Failed to fetch user settings")

    csrf_token = get_or_create_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "settings.html",
        {"user": user, "settings": settings, "csrf_token": csrf_token},
    )
    set_csrf_cookie(response, request, csrf_token)
    return response


@app.post("/settings", include_in_schema=False)
async def post_settings(
    request: Request,
    nickname: str = Form(...),
    preferred_class: str = Form(...),
    csrf_token: str = Form(""),
    user: Dict[str, Any] = Depends(get_current_user),
) -> Response:
    """Save settings via API Gateway then redirect back."""
    validate_csrf_token(request, csrf_token)

    try:
        if not auth_dependencies.LOCAL_AUTH_ENABLED:
            save_user_settings(user["sub"], nickname, preferred_class)
    except Exception:
        logger.exception("Failed to save user settings")

    return RedirectResponse("/settings", status_code=status.HTTP_303_SEE_OTHER)
