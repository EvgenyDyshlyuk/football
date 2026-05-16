import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AWS_REGION", "eu-west-2")
os.environ.setdefault("COGNITO_USER_POOL_ID", "dummy_pool")
os.environ.setdefault("COGNITO_CLIENT_ID", "dummy_client")
os.environ.setdefault("COGNITO_APP_CLIENT_ID", "dummy_client")
os.environ.setdefault("COGNITO_APP_CLIENT_SECRET", "dummy_secret")
os.environ.setdefault("COGNITO_REDIRECT_URI", "http://testserver/")
os.environ.setdefault("COGNITO_AUTH_URL_BASE", "https://example.com/login")
os.environ.setdefault("COGNITO_SCOPE", "openid+profile")

from app.csrf import CSRF_COOKIE  # noqa: E402
from app.main import app  # noqa: E402
from app.routes import matches as matches_routes  # noqa: E402
from app.services import matches as match_service  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_app_state():
    app.dependency_overrides = {}
    client.cookies.clear()
    match_service.clear_matches()
    yield
    app.dependency_overrides = {}
    client.cookies.clear()
    match_service.clear_matches()


@pytest.fixture
def authenticated_user():
    app.dependency_overrides[matches_routes.get_current_user] = (
        lambda token=None, request=None: {"sub": "u1", "username": "u1", "attributes": {}}
    )


def test_matches_page_sets_csrf_cookie(authenticated_user):
    resp = client.get("/matches", headers={"Authorization": "Bearer t"})
    csrf_token = resp.cookies.get(CSRF_COOKIE)

    assert resp.status_code == 200
    assert "Matches" in resp.text
    assert "Create match" in resp.text
    assert "No matches yet." in resp.text
    assert csrf_token
    assert f'name="csrf_token" value="{csrf_token}"' in resp.text


def test_match_create_rejects_missing_csrf(authenticated_user):
    resp = client.post(
        "/matches",
        data={
            "title": "After school five-a-side",
            "starts_at": "2026-06-01T16:00",
            "location": "Park pitch",
            "class_from": "2",
            "class_to": "4",
            "max_players": "10",
            "notes": "Bring water",
        },
        headers={"Authorization": "Bearer t"},
    )

    assert resp.status_code == 403
    assert match_service.list_matches() == []


def test_match_create_redirects_and_appears_in_list(authenticated_user):
    get_resp = client.get("/matches", headers={"Authorization": "Bearer t"})
    csrf_token = get_resp.cookies.get(CSRF_COOKIE)

    post_resp = client.post(
        "/matches",
        data={
            "title": "After school five-a-side",
            "starts_at": "2026-06-01T16:00",
            "location": "Park pitch",
            "class_from": "2",
            "class_to": "4",
            "max_players": "10",
            "notes": "Bring water",
            "csrf_token": csrf_token,
        },
        headers={"Authorization": "Bearer t"},
        follow_redirects=False,
    )

    assert post_resp.status_code == 303
    assert post_resp.headers["location"] == "/matches"

    list_resp = client.get("/matches", headers={"Authorization": "Bearer t"})
    assert "After school five-a-side" in list_resp.text
    assert "Park pitch" in list_resp.text
    assert "Year 2 to Year 4" in list_resp.text
    assert "10 players" in list_resp.text


def test_match_create_rejects_invalid_class_range(authenticated_user):
    get_resp = client.get("/matches", headers={"Authorization": "Bearer t"})
    csrf_token = get_resp.cookies.get(CSRF_COOKIE)

    resp = client.post(
        "/matches",
        data={
            "title": "Backwards class range",
            "starts_at": "2026-06-01T16:00",
            "location": "Park pitch",
            "class_from": "4",
            "class_to": "2",
            "max_players": "10",
            "csrf_token": csrf_token,
        },
        headers={"Authorization": "Bearer t"},
    )

    assert resp.status_code == 400
    assert match_service.list_matches() == []
