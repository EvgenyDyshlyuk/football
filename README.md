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
run setup.sh (poetry will be run according to the setup.sh script)
Adjust settings in `config.ini` if your Cognito details differ.

## Testing
poetry run pytest
poetry run ruff check .

## Running the Application
poetry run uvicorn app.main:app --reload