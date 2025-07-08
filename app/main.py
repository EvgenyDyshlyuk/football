"""Application entry point for the FastAPI application."""

from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.routes import auth_router
import app.core.config  # noqa: F401  # Ensure .env is loaded on startup
from app.config import COGNITO_AUTH_URL
from app.jinja2_env import templates

# Determine this file’s parent dir (i.e. the "app/" folder)
BASE_DIR = Path(__file__).parent

app = FastAPI()

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

    if auth_header or cookie_token or request.query_params.get("code"):
        from app.auth.dependencies import get_current_user

        token = None
        scheme = "Bearer"
        if auth_header:
            scheme, _, token = auth_header.partition(" ")
        else:
            token = cookie_token

        user = None
        if token:
            creds = HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
            try:
                user = get_current_user(token=creds)
            except Exception:
                return RedirectResponse(
                    COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT
                )

        return templates.TemplateResponse(request, "home.html", {"user": user})

    return RedirectResponse(
        COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )
