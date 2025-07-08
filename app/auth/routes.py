from fastapi import APIRouter, Form, Depends, Response, status, Request
from fastapi.responses import RedirectResponse

from app.jinja2_env import templates
from app.auth.cognito import authenticate_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("/login")
async def get_login(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@auth_router.post("/login")
async def post_login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    auth = authenticate_user(username, password)
    if not auth:
        return Response(
            content='<p class="text-red-500">Invalid credentials</p>',
            media_type="text/html",
        )
    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key="access_token",
        value=auth["IdToken"],
        httponly=True,
        secure=True,
    )
    return redirect
