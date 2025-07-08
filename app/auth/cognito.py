import os
import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

client = boto3.client("cognito-idp", region_name=AWS_REGION)


def authenticate_user(username: str, password: str):
    """Attempt ADMIN_NO_SRP_AUTH against Cognito. Returns AuthenticationResult dict
    or None on failure."""
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
