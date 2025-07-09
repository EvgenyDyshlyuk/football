"""Pydantic models used by the authentication routes."""

from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str
