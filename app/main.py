from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.auth.routes import auth_router


app = FastAPI()

app.include_router(auth_router, prefix="/auth")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/auth/login")
