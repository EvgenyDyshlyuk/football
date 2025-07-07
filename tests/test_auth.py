import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app

client = TestClient(app)


def test_login_get():
    response = client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 307
    assert (
        response.headers.get("location")
        == "https://eu-west-2wwv3xqgys.auth.eu-west-2.amazoncognito.com/login?client_id=68al97tfenubl3tc3k4fnii8ob&response_type=code&scope=email+openid+phone&redirect_uri=http%3A%2F%2Flocalhost%3A8000"
    )


def test_login_post_redirect():
    response = client.post("/auth/login", follow_redirects=False)
    assert response.status_code == 307
    assert (
        response.headers.get("location")
        == "https://eu-west-2wwv3xqgys.auth.eu-west-2.amazoncognito.com/login?client_id=68al97tfenubl3tc3k4fnii8ob&response_type=code&scope=email+openid+phone&redirect_uri=http%3A%2F%2Flocalhost%3A8000"
    )


def test_homepage_get():
    response = client.get("/", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    assert "Hello this is homepage" in response.text


def test_homepage_redirect_for_new_user():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert (
        response.headers.get("location")
        == "https://eu-west-2wwv3xqgys.auth.eu-west-2.amazoncognito.com/login?client_id=68al97tfenubl3tc3k4fnii8ob&response_type=code&scope=email+openid+phone&redirect_uri=http%3A%2F%2Flocalhost%3A8000"
    )
