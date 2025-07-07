from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from app.auth.routes import auth_router, COGNITO_AUTH_URL
from app.jinja2_env import templates

app = FastAPI()

app.include_router(auth_router, prefix="/auth")


@app.get("/", include_in_schema=False)
async def root(request: Request):
    if request.headers.get("Authorization") or request.query_params.get("code"):
        return templates.TemplateResponse("home.html", {"request": request})
    return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
