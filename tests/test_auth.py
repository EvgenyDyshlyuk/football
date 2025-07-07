import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app
from app.config import COGNITO_AUTH_URL

client = TestClient(app)


def test_login_get():
    response = client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers.get("location") == COGNITO_AUTH_URL


def test_login_post_redirect():
    response = client.post("/auth/login", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers.get("location") == COGNITO_AUTH_URL


def test_homepage_get():
    response = client.get("/", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    assert "Hello this is homepage" in response.text


def test_homepage_redirect_for_new_user():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers.get("location") == COGNITO_AUTH_URL
