"""Configuration loader for AWS Cognito settings."""
# %%
import os
from urllib.parse import quote_plus

# 1) Load and validate all required Cognito environment variables
COGNITO_AUTH_URL_BASE = os.getenv("COGNITO_AUTH_URL_BASE")
if not COGNITO_AUTH_URL_BASE:
    raise RuntimeError("Missing COGNITO_AUTH_URL_BASE environment variable")

COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
if not COGNITO_CLIENT_ID:
    raise RuntimeError("Missing COGNITO_CLIENT_ID environment variable")

COGNITO_SCOPE = os.getenv("COGNITO_SCOPE")
if not COGNITO_SCOPE:
    raise RuntimeError("Missing COGNITO_SCOPE environment variable")

COGNITO_REDIRECT_URI = os.getenv("COGNITO_REDIRECT_URI")
if not COGNITO_REDIRECT_URI:
    raise RuntimeError("Missing COGNITO_REDIRECT_URI environment variable")

# 2) Encode the redirect URI (this forces the str-overload of quote_plus)
encoded_redirect = quote_plus(COGNITO_REDIRECT_URI, safe="/")

# 3) Build the full Cognito authorization URL
COGNITO_AUTH_URL = (
    f"{COGNITO_AUTH_URL_BASE}"
    f"?client_id={COGNITO_CLIENT_ID}"
    f"&response_type=code"
    f"&scope={COGNITO_SCOPE}"
    f"&redirect_uri={encoded_redirect}"
)

# Example usage printout (remove in production)
if __name__ == "__main__":
    print("Cognito Auth URL:", COGNITO_AUTH_URL)

# %%
