import os
import sys
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
import base64
import importlib
import pytest

os.environ.setdefault("AWS_REGION", "eu-west-2")
os.environ.setdefault("COGNITO_USER_POOL_ID", "dummy_pool")
os.environ.setdefault("COGNITO_CLIENT_ID", "dummy_client")
os.environ.setdefault("COGNITO_APP_CLIENT_ID", "dummy_client")
os.environ.setdefault("COGNITO_APP_CLIENT_SECRET", "dummy_secret")
os.environ.setdefault("COGNITO_REDIRECT_URI", "http://testserver/")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app
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
    # Cookie should not include the Secure flag in local stage
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "Secure" not in set_cookie_header


def test_homepage_get(monkeypatch):
    def fake_get(url):
        class Resp:
            def json(self_inner):
                return {"keys": []}

        return Resp()

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("app.auth.dependencies.get_current_user", lambda token=None: {"sub": "u1"})
    response = client.get("/", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    assert "Hello:" in response.text
    assert "u1" in response.text


def test_homepage_redirect_for_new_user():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers.get("location") == COGNITO_AUTH_URL


def test_homepage_cookie_login(monkeypatch):
    def fake_get(url):
        class Resp:
            def json(self_inner):
                return {"keys": []}

        return Resp()

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr(
        "app.auth.routes.authenticate_user", lambda u, p: {"IdToken": "abc"}
    )
    monkeypatch.setattr(
        "app.auth.dependencies.get_current_user", lambda token=None: {"sub": "u1"}
    )

    login_resp = client.post(
        "/auth/login", data={"username": "good", "password": "pass"}, follow_redirects=False
    )
    assert login_resp.status_code == 303
    cookie = login_resp.cookies.get("access_token")
    assert cookie == "abc"

    client.cookies.set("access_token", cookie)
    response = client.get("/")
    assert response.status_code == 200
    assert "u1" in response.text
    client.cookies.clear()


def test_callback_flow(monkeypatch):
    def fake_post(url, data=None, auth=None, headers=None):
        class Resp:
            def raise_for_status(self_inner):
                pass

            def json(self_inner):
                return {"id_token": "jwt1"}

        return Resp()

    def fake_get(url):
        class Resp:
            def json(self_inner):
                return {"keys": []}

        return Resp()

    monkeypatch.setattr("app.auth.cognito.requests.post", fake_post)
    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr(
        "app.auth.dependencies.get_current_user", lambda token=None: {"sub": "u1"}
    )

    resp = client.get("/?code=abc", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"
    cookie = resp.cookies.get("access_token")
    assert cookie == "jwt1"
    # Cookie should not include Secure flag when STAGE is local
    set_cookie_header = resp.headers.get("set-cookie", "")
    assert "Secure" not in set_cookie_header

    client.cookies.set("access_token", cookie)
    resp2 = client.get("/")
    assert resp2.status_code == 200
    assert "u1" in resp2.text


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

    token = jwt.encode({"sub": "u1", "aud": os.environ["COGNITO_CLIENT_ID"]},
                       "wrong", algorithm="HS256", headers={"kid": "test"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(Exception):
        dependencies.get_current_user(token=creds)
