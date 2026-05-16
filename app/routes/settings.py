"""Routes for user settings."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse, Response

from app.auth import dependencies as auth_dependencies
from app.auth.dependencies import get_current_user
from app.csrf import get_or_create_csrf_token, set_csrf_cookie, validate_csrf_token
from app.jinja2_env import templates
from app.services.user_settings import fetch_user_settings, save_user_settings

logger = logging.getLogger(__name__)

settings_router = APIRouter(tags=["settings"])


@settings_router.get("/settings", include_in_schema=False)
async def get_settings(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    """Render the user settings form populated from API Gateway."""
    settings = (
        {
            "nickname": user.get("attributes", {}).get("nickname", ""),
            "preferred_class": "",
        }
        if auth_dependencies.LOCAL_AUTH_ENABLED
        else {}
    )

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


@settings_router.post("/settings", include_in_schema=False)
async def post_settings(
    request: Request,
    nickname: str = Form(...),
    preferred_class: str = Form(...),
    csrf_token: str = Form(""),
    user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    """Save settings via API Gateway then redirect back."""
    validate_csrf_token(request, csrf_token)

    try:
        if not auth_dependencies.LOCAL_AUTH_ENABLED:
            save_user_settings(user["sub"], nickname, preferred_class)
    except Exception:
        logger.exception("Failed to save user settings")

    return RedirectResponse("/settings", status_code=status.HTTP_303_SEE_OTHER)
