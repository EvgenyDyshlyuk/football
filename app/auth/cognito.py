"""Utility functions for interacting with AWS Cognito."""

import logging
from functools import lru_cache
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError, RequestException

import boto3
from botocore.exceptions import ClientError

from app.config import (
    AWS_REGION,
    COGNITO_APP_CLIENT_ID,
    COGNITO_APP_CLIENT_SECRET,
    COGNITO_AUTH_URL_BASE,
    COGNITO_REDIRECT_URI,
    COGNITO_USER_POOL_ID,
    LOCAL_AUTH_ENABLED,
)

logger = logging.getLogger(__name__)

# ─── Top‐level ENV VAR LOAD & VALIDATION ───────────────────────────────────────

_missing_top = [
    name
    for name, val in [
        ("AWS_REGION", AWS_REGION),
        ("COGNITO_USER_POOL_ID", COGNITO_USER_POOL_ID),
        ("COGNITO_APP_CLIENT_ID", COGNITO_APP_CLIENT_ID),
    ]
    if not val
]
if _missing_top and not LOCAL_AUTH_ENABLED:
    raise RuntimeError(f"Missing environment variables: {', '.join(_missing_top)}")

# Narrowed, non‐None locals for boto3 client and admin auth calls
_aws_region = AWS_REGION or ""
_cognito_user_pool_id = COGNITO_USER_POOL_ID or ""
_cognito_idp_client_id = COGNITO_APP_CLIENT_ID or ""

@lru_cache(maxsize=1)
def get_cognito_client():
    """Create the Cognito client only when an AWS call is actually needed."""
    return boto3.client("cognito-idp", region_name=_aws_region)


# ─── USERNAME/PASSWORD AUTH ────────────────────────────────────────────────────

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Attempt ADMIN_NO_SRP_AUTH against Cognito.

    Returns the `AuthenticationResult` dict or None on failure.
    """
    try:
        resp = get_cognito_client().initiate_auth(
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
        resp = get_cognito_client().admin_get_user(
            UserPoolId=_cognito_user_pool_id,
            Username=username,
        )
    except ClientError:
        logger.exception("Failed to fetch Cognito user attributes")
        return {}

    attrs = {
        attr["Name"]: attr["Value"]
        for attr in resp.get("UserAttributes", [])  # safe because default is []
    }
    logger.debug("Fetched Cognito user attributes: keys=%s", sorted(attrs))
    return attrs


# ─── EXCHANGE CODE FOR TOKENS ─────────────────────────────────────────────────

def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange an OAuth `code` for tokens via Cognito."""

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

    logger.debug("Exchanging Cognito authorization code")

    resp: requests.Response | None = None
    try:
        resp = requests.post(
            token_url,
            data=payload,
            auth=HTTPBasicAuth(client_id_app, client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        resp.raise_for_status()

        tokens = resp.json()
        logger.info("Token exchange succeeded")
        return tokens

    except HTTPError as http_err:
        response = http_err.response or resp
        status_code = response.status_code if response else "N/A"

        logger.error(
            "HTTPError during token exchange (status=%s): %s",
            status_code,
            http_err,
        )
        raise

    except RequestException as req_err:
        logger.error(
            "RequestException during token exchange: %s", req_err, exc_info=True
        )
        raise


# ─── REFRESH ACCESS TOKEN ─────────────────────────────────────────────────────

def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """Use a Cognito refresh token to obtain new tokens."""

    _missing = [
        name
        for name, val in [
            ("COGNITO_AUTH_URL_BASE", COGNITO_AUTH_URL_BASE),
            ("COGNITO_APP_CLIENT_ID", COGNITO_APP_CLIENT_ID),
            ("COGNITO_APP_CLIENT_SECRET", COGNITO_APP_CLIENT_SECRET),
        ]
        if not val
    ]
    if _missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(_missing)}")

    base_url: str = COGNITO_AUTH_URL_BASE  # type: ignore[assignment]
    client_id_app: str = COGNITO_APP_CLIENT_ID  # type: ignore[assignment]
    client_secret: str = COGNITO_APP_CLIENT_SECRET  # type: ignore[assignment]

    token_url = base_url.replace("/login", "/oauth2/token")
    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id_app,
        "refresh_token": refresh_token,
    }

    logger.debug("Refreshing Cognito access token")

    resp: requests.Response | None = None
    try:
        resp = requests.post(
            token_url,
            data=payload,
            auth=HTTPBasicAuth(client_id_app, client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        resp.raise_for_status()
        tokens = resp.json()
        logger.info("Refresh token succeeded")
        return tokens
    except HTTPError as http_err:
        response = http_err.response or resp
        status_code = response.status_code if response else "N/A"
        logger.error(
            "HTTPError during token refresh (status=%s): %s",
            status_code,
            http_err,
        )
        raise
    except RequestException as req_err:
        logger.error(
            "RequestException during token refresh: %s", req_err, exc_info=True
        )
        raise
    except Exception:
        logger.error("Unexpected error in refresh_access_token", exc_info=True)
        raise
