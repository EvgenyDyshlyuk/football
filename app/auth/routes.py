from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.jinja2_env import templates
from .schemas import UserLogin

auth_router = APIRouter()


def login_form(
    username: str = Form(...),
    password: str = Form(...),
) -> UserLogin:
    return UserLogin(username=username, password=password)


@auth_router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@auth_router.post("/login")
async def login_post(form: UserLogin = Depends(login_form)):
    if form.username == "admin" and form.password == "secret":
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return HTMLResponse(
        '<p class="text-red-500">Invalid credentials</p>',
        status_code=status.HTTP_200_OK,
    )

