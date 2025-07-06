import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app

client = TestClient(app)

def test_login_get():
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_login_post_valid():
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "secret"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers.get("location") == "/"


def test_login_post_invalid():
    response = client.post(
        "/auth/login",
        data={"username": "user", "password": "wrong"},
    )
    assert response.status_code == 200
    assert "Invalid credentials" in response.text
