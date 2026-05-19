# Agent Guidelines for the Football Repository

This repository uses **Poetry** for Python dependencies and **npm** for front-end assets.
Before running tests or the application, ensure your environment is set up using `setup.sh`
or that Poetry and Node are installed.

## Directory Overview
- `app/` - FastAPI application code
- `app/auth/` - Cognito-based authentication helpers and routes
- `app/routes/` - HTTP route modules
- `app/services/` - business logic and external persistence clients
- `app/templates/` - Jinja2 templates
- `app/static/` - Static assets (CSS/JS) built via Tailwind
- `infra/` - AWS infrastructure templates
- `tests/` - Pytest test suite
- `.env.template` - Example environment configuration values

## Recommended Workflow
1. **Install dependencies**
   ```bash
   ./setup.sh
   ```
   This script installs Python (via Poetry) and Node requirements.

   Real .env file contains secrets so is added to .gitignore, so create your own from .env.template file:
   ```bash
   cp .env.template .env
   ```

2. **Run tests and linters** before committing:
   ```bash
   poetry run ruff check .
   poetry run pytest
   ```

3. **Build CSS** whenever you modify Tailwind sources or templates:
   ```bash
   npm run build:css
   ```

4. **Run the development server** with:
   ```bash
   poetry run uvicorn app.main:app --reload --log-level debug
   ```

   For local UI-only work without DynamoDB, explicitly set `MATCHES_USE_MEMORY=true`.
   This is only for `STAGE=local`; do not use memory storage in production-like runs.

## DynamoDB Match Storage
Match persistence uses DynamoDB when `MATCHES_TABLE_NAME` is set. Tests inject an
in-memory repository explicitly; the application should not silently fall back to
memory storage for real runtime paths.

Matches table schema:

```text
PK  string partition key
SK  string sort key
GSI1PK string partition key for GSI1
GSI1SK string sort key for GSI1
```

Match items use:

```text
PK          MATCH
SK          START#<starts_at_iso>#<match_id>
GSI1PK      USER#<creator_sub>
GSI1SK      START#<starts_at_iso>#<match_id>
```

Use `infra/dynamodb-matches-table.yaml` to create the table shape.

## Local Auth Bypass
For local development, the app supports a dummy authenticated user so agents do not need real Cognito credentials.
This is controlled by `.env` and only works when `STAGE=local`:

```bash
LOCAL_AUTH_ENABLED=true
LOCAL_AUTH_SUB=local-test-user
LOCAL_AUTH_EMAIL=test-codex@example.com
LOCAL_AUTH_USERNAME=test-codex@example.com
LOCAL_AUTH_NICKNAME=Codex Test
```

When this is enabled, `/`, `/matches`, `/settings`, `/auth/login`, and `/auth/logout` use the dummy local user.
Never enable `LOCAL_AUTH_ENABLED` outside local development.

Keep commits focused and run the commands above to ensure code quality.
