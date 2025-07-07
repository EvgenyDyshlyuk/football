from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

COGNITO_AUTH_URL = (
    "https://eu-west-2wwv3xqgys.auth.eu-west-2.amazoncognito.com/login?"
    "client_id=68al97tfenubl3tc3k4fnii8ob&response_type=code&"
    "scope=email+openid+phone&redirect_uri=http%3A%2F%2Flocalhost%3A8000"
)

auth_router = APIRouter()


@auth_router.get("/login")
async def login_get():
    return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.post("/login")
async def login_post():
    return RedirectResponse(COGNITO_AUTH_URL, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
