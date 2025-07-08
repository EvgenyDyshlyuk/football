import os
import sys
from fastapi.testclient import TestClient

os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("COGNITO_USER_POOL_ID", "dummy_pool")
os.environ.setdefault("COGNITO_CLIENT_ID", "dummy_client")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app
from app.auth import cognito
from app.config import COGNITO_AUTH_URL

client = TestClient(app)


def test_login_get():
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert "Username" in response.text


def test_login_post_invalid(monkeypatch):
    monkeypatch.setattr("app.auth.routes.authenticate_user", lambda u, p: None)
    response = client.post("/auth/login", data={"username": "bad", "password": "pass"})
    assert response.status_code == 200
    assert "Invalid credentials" in response.text


def test_login_post_success(monkeypatch):
    monkeypatch.setattr("app.auth.routes.authenticate_user", lambda u, p: {"IdToken": "abc"})
    response = client.post("/auth/login", data={"username": "good", "password": "pass"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers.get("location") == "/"
    assert response.cookies.get("access_token") == "abc"


def test_homepage_get():
    response = client.get("/", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    assert "Hello this is homepage" in response.text


def test_homepage_redirect_for_new_user():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers.get("location") == COGNITO_AUTH_URL
