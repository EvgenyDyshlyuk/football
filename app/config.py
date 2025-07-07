from configparser import ConfigParser
from pathlib import Path
from urllib.parse import quote_plus

_config = ConfigParser()
_config.read(Path(__file__).resolve().parent.parent / "config.ini")

COGNITO_AUTH_URL_BASE = _config.get("cognito", "auth_url_base")
COGNITO_CLIENT_ID = _config.get("cognito", "client_id")
COGNITO_SCOPE = _config.get("cognito", "scope")
COGNITO_REDIRECT_URI = _config.get("cognito", "redirect_uri")

COGNITO_AUTH_URL = (
    f"{COGNITO_AUTH_URL_BASE}?client_id={COGNITO_CLIENT_ID}&response_type=code&"
    f"scope={COGNITO_SCOPE}&redirect_uri={quote_plus(COGNITO_REDIRECT_URI)}"
)
