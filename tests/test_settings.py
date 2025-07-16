import requests


class Resp:
    status_code = 200

    def json(self):
        return {"nickname": "nick", "preferred_class": "1"}

    def raise_for_status(self):
        pass

requests.get = lambda url, timeout=10: Resp()

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
import app.main as app_main  # noqa: E402

client = TestClient(app)


def test_settings_page(monkeypatch):
    app.dependency_overrides[app_main.get_current_user] = (
        lambda token=None, request=None: {"sub": "u1", "username": "u1", "attributes": {}}
    )

    resp = client.get("/settings", headers={"Authorization": "Bearer t"})
    assert resp.status_code == 200
    assert "User Settings" in resp.text
    app.dependency_overrides = {}
