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

## Testing
poetry run pytest
poetry run ruff check .

## Running the Application
poetry run uvicorn app.main:app --reload --log-level debug
