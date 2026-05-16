# Football App

A simple football application that allows users to register, login, and manage their favorite teams.

This is stage-by-stage implementataion of a football application using FastAPI, AWS Cognito for authentication.

In this stage, the application allows users to register and login using AWS Cognito.

## Features
Secure, managed credentials via Cognito (no custom password storage).
JWT-based sessions with automatic refresh support.
A fully server-rendered, Alpine/HTMX-enhanced UI served by S3/CloudFront for maximum performance.
Your FastAPI code running in a Lambda container, scaling to zero when idle.

## Setup
Run `setup.sh` to install Poetry and Node dependencies.
Copy `.env.template` to `.env` and replace the placeholder Cognito values with your own.
At a minimum `COGNITO_CLIENT_ID`, `COGNITO_AUTH_URL_BASE`, `COGNITO_SCOPE`, and `COGNITO_REDIRECT_URI`
must be provided or the application will not start.

## Local Auth Bypass
For local UI and settings development, you can use a dummy user instead of signing in through Cognito.
This only works when `STAGE=local`.

Set these values in `.env`:

```bash
LOCAL_AUTH_ENABLED=true
LOCAL_AUTH_SUB=local-test-user
LOCAL_AUTH_EMAIL=test-codex@example.com
LOCAL_AUTH_USERNAME=test-codex@example.com
LOCAL_AUTH_NICKNAME=Codex Test
```

With local auth enabled, `/`, `/settings`, `/auth/login`, and `/auth/logout` use the dummy user locally.
Do not enable this outside local development.

## Testing
poetry run pytest
poetry run ruff check .

## Running the Application
poetry run uvicorn app.main:app --reload --log-level debug
