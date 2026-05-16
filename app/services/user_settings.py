"""Persistence client for user settings."""

from __future__ import annotations

import os
from typing import Any

import requests

AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
API_GATEWAY_ID = os.getenv("API_GATEWAY_ID")


def _api_base() -> str:
    if not API_GATEWAY_ID:
        raise RuntimeError("API_GATEWAY_ID environment variable is not set")
    return f"https://{API_GATEWAY_ID}.execute-api.{AWS_REGION}.amazonaws.com"


def fetch_user_settings(sub: str) -> dict[str, Any]:
    """Fetch saved settings for a user."""
    url = f"{_api_base()}/user/{sub}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()
    return resp.json()


def save_user_settings(sub: str, nickname: str, preferred_class: str) -> None:
    """Persist user settings."""
    url = f"{_api_base()}/user/{sub}"
    payload = {"nickname": nickname, "preferred_class": preferred_class}
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
