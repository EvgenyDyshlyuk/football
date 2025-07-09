"""Utility functions for interacting with AWS Cognito."""

import os
from typing import Any, Dict, Optional
import logging

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError, RequestException

from app.config import COGNITO_AUTH_URL_BASE, COGNITO_REDIRECT_URI
from app.core.config import COGNITO_APP_CLIENT_ID, COGNITO_APP_CLIENT_SECRET

import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

client = boto3.client("cognito-idp", region_name=AWS_REGION)

logger = logging.getLogger(__name__)


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Attempt ADMIN_NO_SRP_AUTH against Cognito.

    Returns the ``AuthenticationResult`` dictionary or ``None`` on failure.
    """
    try:
        resp = client.initiate_auth(
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
            ClientId=COGNITO_CLIENT_ID,
            UserPoolId=COGNITO_USER_POOL_ID,
        )
        return resp["AuthenticationResult"]
    except ClientError:
        return None


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange an OAuth `code` for tokens via Cognito, with robust debug/error output."""
    token_url = COGNITO_AUTH_URL_BASE.replace("/login", "/oauth2/token")
    payload = {
        "grant_type": "authorization_code",
        "client_id": COGNITO_APP_CLIENT_ID,
        "code": code,
        "redirect_uri": COGNITO_REDIRECT_URI,
    }

    logger.debug("Token request URL: %s", token_url)
    logger.debug("Token request payload: %r", payload)

    resp = None
    try:
        resp = requests.post(
            token_url,
            data=payload,
            auth=HTTPBasicAuth(COGNITO_APP_CLIENT_ID, COGNITO_APP_CLIENT_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        logger.debug("HTTP %s received", resp.status_code)
        logger.debug("Response headers: %r", resp.headers)
        logger.debug("Raw response body: %s", resp.text)

        # This may raise HTTPError for 4xx/5xx
        resp.raise_for_status()

        tokens = resp.json()
        logger.info("Token exchange succeeded, keys: %s", list(tokens.keys()))
        return tokens

    except HTTPError as http_err:
        # Prefer the response attached to the exception, fallback to resp
        response = getattr(http_err, "response", None) or resp
        status = getattr(response, "status_code", "N/A")
        try:
            body = response.json()
        except Exception:
            body = response.text if response is not None else "<no response body>"
        logger.error(
            "HTTPError during token exchange (status=%s): %s\nResponse body: %r",
            status,
            http_err,
            body,
        )
        raise

    except RequestException as req_err:
        # Network issues, DNS problems, timeouts, etc.
        logger.error("RequestException during token exchange: %s", req_err, exc_info=True)
        raise

    except Exception:
        logger.error(
            "Unexpected error in exchange_code_for_tokens",
            exc_info=True,
        )
        raise
