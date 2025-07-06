from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse

from .schemas import UserLogin

COGNITO_AUTH_URL = (
    "https://eu-west-2wwv3xqgys.auth.eu-west-2.amazoncognito.com/login?"
    "client_id=68al97tfenubl3tc3k4fnii8ob&response_type=code&"
    "scope=email+openid+phone&redirect_uri=http%3A%2F%2Flocalhost%3A8000"
)

auth_router = APIRouter()


def login_form(
    username: str = Form(...),
    password: str = Form(...),
) -> UserLogin:
    return UserLogin(username=username, password=password)


@auth_router.get("/login")
async def login_get():
    return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.post("/login")
async def login_post(form: UserLogin = Depends(login_form)):
    if form.username == "admin" and form.password == "secret":
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return HTMLResponse(
        '<p class="text-red-500">Invalid credentials</p>',
        status_code=status.HTTP_200_OK,
    )

