"""Utility functions for interacting with AWS Cognito."""

import os
import logging
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError, RequestException

import boto3
from botocore.exceptions import ClientError

from app.config import (
    COGNITO_APP_CLIENT_ID,
    COGNITO_APP_CLIENT_SECRET,
    COGNITO_AUTH_URL_BASE,
    COGNITO_REDIRECT_URI,
)

logger = logging.getLogger(__name__)

# ─── Top‐level ENV VAR LOAD & VALIDATION ───────────────────────────────────────

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

_missing_top = [
    name
    for name, val in [
        ("AWS_REGION", AWS_REGION),
        ("COGNITO_USER_POOL_ID", COGNITO_USER_POOL_ID),
        ("COGNITO_CLIENT_ID", COGNITO_CLIENT_ID),
    ]
    if not val
]
if _missing_top:
    raise RuntimeError(f"Missing environment variables: {', '.join(_missing_top)}")

# Narrowed, non‐None locals for boto3 client and admin auth calls
_aws_region: str = AWS_REGION  # type: ignore[assignment]
_cognito_user_pool_id: str = COGNITO_USER_POOL_ID  # type: ignore[assignment]
_cognito_idp_client_id: str = COGNITO_CLIENT_ID  # type: ignore[assignment]

# Boto3 client for user‐pool operations
client = boto3.client("cognito-idp", region_name=_aws_region)


# ─── USERNAME/PASSWORD AUTH ────────────────────────────────────────────────────

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Attempt ADMIN_NO_SRP_AUTH against Cognito.

    Returns the `AuthenticationResult` dict or None on failure.
    """
    try:
        resp = client.initiate_auth(
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
            ClientId=_cognito_idp_client_id,
            UserPoolId=_cognito_user_pool_id,
        )
        return resp.get("AuthenticationResult")
    except ClientError:
        return None


# ─── FETCH USER ATTRIBUTES ────────────────────────────────────────────────────

def fetch_user_attributes(username: str) -> Dict[str, Any]:
    """Retrieve a user's attributes from Cognito using their username."""
    try:
        resp = client.admin_get_user(
            UserPoolId=_cognito_user_pool_id,
            Username=username,
        )
    except ClientError:
        logger.exception("Failed to fetch attributes for %s", username)
        return {}

    attrs = {
        attr["Name"]: attr["Value"]
        for attr in resp.get("UserAttributes", [])  # safe because default is []
    }
    logger.debug("Fetched attributes for %s: %r", username, attrs)
    return attrs


# ─── EXCHANGE CODE FOR TOKENS ─────────────────────────────────────────────────

def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange an OAuth `code` for tokens via Cognito, with robust debug/error output."""

    # Validate imported config values
    _missing = [
        name
        for name, val in [
            ("COGNITO_AUTH_URL_BASE", COGNITO_AUTH_URL_BASE),
            ("COGNITO_APP_CLIENT_ID", COGNITO_APP_CLIENT_ID),
            ("COGNITO_APP_CLIENT_SECRET", COGNITO_APP_CLIENT_SECRET),
            ("COGNITO_REDIRECT_URI", COGNITO_REDIRECT_URI),
        ]
        if not val
    ]
    if _missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(_missing)}")

    # Narrow to local str vars
    base_url: str = COGNITO_AUTH_URL_BASE  # type: ignore[assignment]
    client_id_app: str = COGNITO_APP_CLIENT_ID  # type: ignore[assignment]
    client_secret: str = COGNITO_APP_CLIENT_SECRET  # type: ignore[assignment]
    redirect_uri: str = COGNITO_REDIRECT_URI  # type: ignore[assignment]

    # Build endpoint & payload
    token_url = base_url.replace("/login", "/oauth2/token")
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id_app,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    logger.debug("Token request URL: %s", token_url)
    logger.debug("Token request payload: %r", payload)

    resp: requests.Response | None = None
    try:
        resp = requests.post(
            token_url,
            data=payload,
            auth=HTTPBasicAuth(client_id_app, client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        logger.debug("HTTP %s received", resp.status_code)
        logger.debug("Response headers: %r", resp.headers)
        logger.debug("Raw response body: %s", resp.text)

        resp.raise_for_status()

        tokens = resp.json()
        logger.info("Token exchange succeeded, keys: %s", list(tokens.keys()))
        return tokens

    except HTTPError as http_err:
        response = http_err.response or resp
        status_code = response.status_code if response else "N/A"

        if response is not None:
            try:
                body = response.json()
            except Exception:
                body = response.text
        else:
            body = "<no response>"

        logger.error(
            "HTTPError during token exchange (status=%s): %s\nResponse body: %r",
            status_code,
            http_err,
            body,
        )
        raise

    except RequestException as req_err:
        logger.error(
            "RequestException during token exchange: %s", req_err, exc_info=True
        )
        raise

    except Exception:
        logger.error("Unexpected error in exchange_code_for_tokens", exc_info=True)
        raise
