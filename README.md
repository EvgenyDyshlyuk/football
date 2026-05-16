# Football App

A FastAPI application for children and families to organise local football matches.
The app uses server-rendered Jinja pages, AWS Cognito authentication, CSRF-protected
forms, and DynamoDB-backed match storage.

## Current Features

- Cognito Hosted UI login/logout flow.
- Local auth bypass for development only.
- User settings page.
- Match list and match creation page.
- DynamoDB repository for match persistence.
- Tailwind CSS build pipeline.

## Setup

Run `setup.sh` to install Poetry and Node dependencies:

```bash
./setup.sh
```

Create a local environment file:

```bash
cp .env.template .env
```

Then replace the placeholder Cognito, API Gateway, and DynamoDB values.

At minimum, a real runtime needs:

```bash
AWS_REGION=eu-west-2
COGNITO_REGION=eu-west-2
COGNITO_USER_POOL_ID=...
COGNITO_APP_CLIENT_ID=...
COGNITO_APP_CLIENT_SECRET=...
COGNITO_CLIENT_ID=...
COGNITO_AUTH_URL_BASE=https://.../login
COGNITO_SCOPE=email+openid+phone
COGNITO_REDIRECT_URI=http://localhost:8001/
MATCHES_TABLE_NAME=football-matches-dev
```

## AWS Schema

### Cognito

The app expects an AWS Cognito user pool and app client. The Hosted UI redirects
back to `COGNITO_REDIRECT_URI`, where the app exchanges the OAuth code for tokens.
Access and refresh tokens are stored in `HttpOnly`, `SameSite=lax` cookies.

### DynamoDB Matches Table

The match repository uses DynamoDB when `MATCHES_TABLE_NAME` is set.

Table keys:

```text
PK  string partition key
SK  string sort key
```

Global secondary index:

```text
GSI1
  GSI1PK string partition key
  GSI1SK string sort key
```

Match item shape:

```text
PK          MATCH
SK          START#<starts_at_iso>#<match_id>
GSI1PK      USER#<creator_sub>
GSI1SK      START#<starts_at_iso>#<match_id>
match_id    <uuid>
creator_sub <cognito_sub>
title       <match title>
starts_at   <ISO datetime>
location    <location text>
class_from  reception | 1 | 2 | 3 | 4 | 5 | 6
class_to    reception | 1 | 2 | 3 | 4 | 5 | 6
max_players <integer>
notes       <optional notes>
```

Current access patterns:

- List upcoming matches: query `PK = MATCH`, sorted by `SK`.
- Create match: put one match item.
- Future "my matches" view: query `GSI1PK = USER#<creator_sub>`.

A starter CloudFormation template is available at
`infra/dynamodb-matches-table.yaml`.

## Local Development

Preferred local development uses real AWS dev resources:

```bash
LOCAL_AUTH_ENABLED=true MATCHES_TABLE_NAME=football-matches-dev poetry run uvicorn app.main:app --reload --log-level debug --port 8001
```

Then open:

```text
http://127.0.0.1:8001/
http://127.0.0.1:8001/matches
http://127.0.0.1:8001/settings
```

For local-only UI work without DynamoDB, explicitly set:

```bash
MATCHES_USE_MEMORY=true
```

This in-memory mode is only for development and tests. It resets when the server
restarts and should not be enabled outside `STAGE=local`.

## Local Auth Bypass

For local UI development, you can use a dummy user instead of signing in through
Cognito. This only works when `STAGE=local`.

Set these values in `.env`:

```bash
LOCAL_AUTH_ENABLED=true
LOCAL_AUTH_SUB=local-test-user
LOCAL_AUTH_EMAIL=test-codex@example.com
LOCAL_AUTH_USERNAME=test-codex@example.com
LOCAL_AUTH_NICKNAME=Codex Test
```

With local auth enabled, `/`, `/matches`, `/settings`, `/auth/login`, and
`/auth/logout` use the dummy user locally.

## Testing

```bash
poetry run ruff check .
poetry run pytest
```

Build CSS whenever templates or Tailwind classes change:

```bash
npm run build:css
```
