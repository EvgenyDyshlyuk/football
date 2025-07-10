"""Application entry point for the FastAPI application."""

from pathlib import Path

import logging
from app.logger import configure_logging
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPAuthorizationCredentials
from app.auth.routes import auth_router
from app.config import COGNITO_AUTH_URL
from app.jinja2_env import templates
from app.auth.cognito import exchange_code_for_tokens
from app.auth.middleware import RefreshTokenMiddleware

REFRESH_TOKEN_MAX_AGE = 30 * 24 * 60 * 60  # 30 days

configure_logging()

logger = logging.getLogger(__name__)

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
    cookie_token = request.cookies.get("access_token")
    code = request.query_params.get("code")

    logger.debug("Incoming cookies: %r", dict(request.cookies))
    logger.debug("Authorization header: %s", auth_header)
    logger.debug("Cookie token preview: %s", f"{cookie_token[:10]}..." if cookie_token else None)
    logger.debug("Query code: %s", code)

    # If Cognito redirected back with a code, exchange and set cookie
    if code:
        tokens = exchange_code_for_tokens(code)
        access_token = tokens.get("access_token") or tokens.get("id_token")
        refresh_token = tokens.get("refresh_token")
        if not access_token:
            raise RuntimeError("Cognito did not return an access or ID token")

        redirect = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
        secure_flag = request.url.scheme == "https"
        redirect.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=secure_flag,
        )
        if refresh_token:
            redirect.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=secure_flag,
                max_age=REFRESH_TOKEN_MAX_AGE,
            )
        logger.debug("Setting access_token cookie, secure=%s", secure_flag)
        return redirect

    # If we have credentials in header or cookie, validate and show home
    if auth_header or cookie_token:
        from app.auth.dependencies import get_current_user

        scheme = "Bearer"
        token = cookie_token or ""
        if auth_header:
            scheme, _, token = auth_header.partition(" ")

        user = None
        if token:
            creds = HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
            try:
                user = get_current_user(request=request, token=creds)
            except Exception:
                return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

        logger.debug("User payload from token: %r", user)
        # TemplateResponse now expects the request first
        return templates.TemplateResponse(request, "home.html", {"user": user})

    # No code, no creds → start login
    return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
