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
    match_service.set_match_repository(match_service.InMemoryMatchRepository())
    yield
    app.dependency_overrides = {}
    client.cookies.clear()
    match_service.set_match_repository(None)


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


def test_matches_page_reports_unconfigured_storage(monkeypatch, authenticated_user):
    match_service.set_match_repository(None)
    monkeypatch.setattr(match_service, "MATCHES_TABLE_NAME", None)
    monkeypatch.setattr(match_service, "MATCHES_USE_MEMORY", False)

    resp = client.get("/matches", headers={"Authorization": "Bearer t"})

    assert resp.status_code == 503
    assert "Match storage is unavailable." in resp.text
    assert "Match storage is not configured" in resp.text
    assert "Create match" not in resp.text


def test_match_create_reports_storage_failure(monkeypatch, authenticated_user):
    get_resp = client.get("/matches", headers={"Authorization": "Bearer t"})
    csrf_token = get_resp.cookies.get(CSRF_COOKIE)
    monkeypatch.setattr(
        matches_routes,
        "create_match",
        lambda **kwargs: (_ for _ in ()).throw(
            match_service.MatchStorageError("Unable to save match")
        ),
    )

    resp = client.post(
        "/matches",
        data={
            "title": "After school five-a-side",
            "starts_at": "2026-06-01T16:00",
            "location": "Park pitch",
            "class_from": "2",
            "class_to": "4",
            "max_players": "10",
            "csrf_token": csrf_token,
        },
        headers={"Authorization": "Bearer t"},
    )

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Unable to save match"


def test_dynamodb_repository_stores_match_items():
    class FakeTable:
        def __init__(self):
            self.items = []

        def put_item(self, Item):
            self.items.append(Item)

        def query(self, **kwargs):
            return {"Items": self.items}

    table = FakeTable()
    repository = match_service.DynamoDBMatchRepository(table)
    match = match_service.Match(
        id="",
        creator_sub="u1",
        title="After school five-a-side",
        starts_at=match_service.datetime.fromisoformat("2026-06-01T16:00"),
        location="Park pitch",
        class_from="2",
        class_to="4",
        max_players=10,
        notes="Bring water",
    )

    created = repository.create(match)
    listed = repository.list()

    assert created.id
    assert listed == [created]
    assert table.items[0]["PK"] == "MATCH"
    assert table.items[0]["SK"] == f"START#2026-06-01T16:00:00#{created.id}"
    assert table.items[0]["GSI1PK"] == "USER#u1"
    assert table.items[0]["GSI1SK"] == table.items[0]["SK"]


def test_match_repository_requires_explicit_backend(monkeypatch):
    match_service.set_match_repository(None)
    monkeypatch.setattr(match_service, "MATCHES_TABLE_NAME", None)
    monkeypatch.setattr(match_service, "MATCHES_USE_MEMORY", False)

    with pytest.raises(
        match_service.MatchStorageNotConfiguredError,
        match="Match storage is not configured",
    ):
        match_service.get_match_repository()
