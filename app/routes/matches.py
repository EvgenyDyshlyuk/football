"""Routes for local football matches."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response

from app.auth.dependencies import get_current_user
from app.csrf import get_or_create_csrf_token, set_csrf_cookie, validate_csrf_token
from app.jinja2_env import templates
from app.services.matches import (
    CLASS_OPTIONS,
    create_match,
    format_class,
    list_matches,
)

matches_router = APIRouter(tags=["matches"])


@matches_router.get("/matches", include_in_schema=False)
async def get_matches(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    """Render the match list and creation form."""
    csrf_token = get_or_create_csrf_token(request)
    class_options = [(value, format_class(value)) for value in CLASS_OPTIONS]
    response = templates.TemplateResponse(
        request,
        "matches.html",
        {
            "user": user,
            "matches": list_matches(),
            "class_options": class_options,
            "csrf_token": csrf_token,
        },
    )
    set_csrf_cookie(response, request, csrf_token)
    return response


@matches_router.post("/matches", include_in_schema=False)
async def post_match(
    request: Request,
    title: str = Form(...),
    starts_at: str = Form(...),
    location: str = Form(...),
    class_from: str = Form(...),
    class_to: str = Form(...),
    max_players: int = Form(...),
    notes: str = Form(""),
    csrf_token: str = Form(""),
    user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    """Create a local match then redirect to the list."""
    validate_csrf_token(request, csrf_token)

    try:
        starts_at_value = datetime.fromisoformat(starts_at)
        create_match(
            creator_sub=user["sub"],
            title=title,
            starts_at=starts_at_value,
            location=location,
            class_from=class_from,
            class_to=class_to,
            max_players=max_players,
            notes=notes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return RedirectResponse("/matches", status_code=status.HTTP_303_SEE_OTHER)
