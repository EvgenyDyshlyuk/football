import os
import sys
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
import base64
import importlib
import pytest

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


def test_get_current_user_valid(monkeypatch):
    secret = "secret"
    jwks = {
        "keys": [
            {
                "kty": "oct",
                "kid": "test",
                "k": base64.urlsafe_b64encode(secret.encode()).decode().rstrip("="),
                "alg": "HS256",
            }
        ]
    }

    def fake_get(url):
        class Resp:
            def json(self_inner):
                return jwks

        return Resp()

    monkeypatch.setattr("requests.get", fake_get)
    sys.modules.pop("app.auth.dependencies", None)
    dependencies = importlib.import_module("app.auth.dependencies")

    token = jwt.encode({"sub": "u1", "aud": os.environ["COGNITO_CLIENT_ID"]}, secret, algorithm="HS256", headers={"kid": "test"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    payload = dependencies.get_current_user(token=creds)
    assert payload["sub"] == "u1"


def test_get_current_user_invalid(monkeypatch):
    secret = "secret"
    jwks = {
        "keys": [
            {
                "kty": "oct",
                "kid": "test",
                "k": base64.urlsafe_b64encode(secret.encode()).decode().rstrip("="),
                "alg": "HS256",
            }
        ]
    }

    def fake_get(url):
        class Resp:
            def json(self_inner):
                return jwks

        return Resp()

    monkeypatch.setattr("requests.get", fake_get)
    sys.modules.pop("app.auth.dependencies", None)
    dependencies = importlib.import_module("app.auth.dependencies")

    token = jwt.encode({"sub": "u1", "aud": os.environ["COGNITO_CLIENT_ID"]}, "wrong", algorithm="HS256", headers={"kid": "test"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(Exception):
        dependencies.get_current_user(token=creds)
