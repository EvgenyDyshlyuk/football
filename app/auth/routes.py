from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

from app.config import COGNITO_AUTH_URL

auth_router = APIRouter()


@auth_router.get("/login")
async def login_get():
    return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.post("/login")
async def login_post():
    return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
