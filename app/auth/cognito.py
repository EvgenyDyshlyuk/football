"""Utility functions for interacting with AWS Cognito."""

import os
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth

from app.config import COGNITO_AUTH_URL_BASE, COGNITO_REDIRECT_URI
from app.core.config import COGNITO_APP_CLIENT_ID, COGNITO_APP_CLIENT_SECRET

import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

client = boto3.client("cognito-idp", region_name=AWS_REGION)


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
    """Exchange an OAuth ``code`` for tokens via Cognito."""

    token_url = COGNITO_AUTH_URL_BASE.replace("/login", "/oauth2/token")
    resp = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "client_id": COGNITO_APP_CLIENT_ID,
            "code": code,
            "redirect_uri": COGNITO_REDIRECT_URI,
        },
        auth=HTTPBasicAuth(COGNITO_APP_CLIENT_ID, COGNITO_APP_CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    return resp.json()
