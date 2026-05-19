import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AWS_REGION", "eu-west-2")
os.environ.setdefault("COGNITO_USER_POOL_ID", "dummy_pool")
os.environ.setdefault("COGNITO_APP_CLIENT_ID", "dummy_client")
os.environ.setdefault("COGNITO_APP_CLIENT_SECRET", "dummy_secret")
os.environ.setdefault("COGNITO_REDIRECT_URI", "http://testserver/")
os.environ.setdefault("COGNITO_AUTH_URL_BASE", "https://example.com/login")
os.environ.setdefault("COGNITO_SCOPE", "openid+profile")

from app.csrf import CSRF_COOKIE  # noqa: E402
from app.main import app  # noqa: E402
from app.routes import settings as settings_routes  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_app_state(monkeypatch):
    app.dependency_overrides = {}
    client.cookies.clear()
    monkeypatch.setattr(settings_routes.auth_dependencies, "LOCAL_AUTH_ENABLED", False)
    yield
    app.dependency_overrides = {}
    client.cookies.clear()


@pytest.fixture
def authenticated_user():
    app.dependency_overrides[settings_routes.get_current_user] = (
        lambda token=None, request=None: {"sub": "u1", "username": "u1", "attributes": {}}
    )


def test_settings_page_sets_csrf_cookie(monkeypatch, authenticated_user):
    monkeypatch.setattr(
        settings_routes,
        "fetch_user_settings",
        lambda sub: {"nickname": "nick", "preferred_class": "1"},
    )

    resp = client.get("/settings", headers={"Authorization": "Bearer t"})
    csrf_token = resp.cookies.get(CSRF_COOKIE)

    assert resp.status_code == 200
    assert "User Settings" in resp.text
    assert csrf_token
    assert f'name="csrf_token" value="{csrf_token}"' in resp.text
    set_cookie_header = resp.headers.get("set-cookie", "")
    assert "csrf_token=" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
    assert "SameSite=lax" in set_cookie_header


def test_settings_post_rejects_missing_csrf(authenticated_user):
    resp = client.post(
        "/settings",
        data={"nickname": "Alex", "preferred_class": "2"},
        headers={"Authorization": "Bearer t"},
    )

    assert resp.status_code == 403


def test_settings_post_saves_with_valid_csrf(monkeypatch, authenticated_user):
    saved_settings = []

    monkeypatch.setattr(
        settings_routes,
        "fetch_user_settings",
        lambda sub: {"nickname": "nick", "preferred_class": "1"},
    )
    monkeypatch.setattr(
        settings_routes,
        "save_user_settings",
        lambda sub, nickname, preferred_class: saved_settings.append(
            (sub, nickname, preferred_class)
        ),
    )

    get_resp = client.get("/settings", headers={"Authorization": "Bearer t"})
    csrf_token = get_resp.cookies.get(CSRF_COOKIE)
    post_resp = client.post(
        "/settings",
        data={
            "nickname": "Alex",
            "preferred_class": "2",
            "csrf_token": csrf_token,
        },
        headers={"Authorization": "Bearer t"},
        follow_redirects=False,
    )

    assert post_resp.status_code == 303
    assert post_resp.headers["location"] == "/settings"
    assert saved_settings == [("u1", "Alex", "2")]
