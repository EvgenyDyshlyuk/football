from fastapi import FastAPI, Request

from app.auth.routes import auth_router
from app.jinja2_env import templates

app = FastAPI()

app.include_router(auth_router, prefix="/auth")


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
