from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.auth.routes import auth_router
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
async def root(request: Request):
    """
    If the user has an Authorization header or a Cognito 'code' param,
    render home.html; otherwise kick them to the Cognito login URL.
    """
    if request.headers.get("Authorization") or request.query_params.get("code"):
        return templates.TemplateResponse(request, "home.html")
    return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
