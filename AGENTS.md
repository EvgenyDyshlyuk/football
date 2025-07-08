# Agent Guidelines for the Football Repository

This repository uses **Poetry** for Python dependencies and **npm** for front-end assets. Before running tests or the application, ensure your environment is set up using `setup.sh` or that Poetry and Node are installed.

## Directory Overview
- `app/` - FastAPI application code
- `app/auth/` - Cognito-based authentication helpers and routes
- `app/templates/` - Jinja2 templates
- `app/static/` - Static assets (CSS/JS) built via Tailwind
- `tests/` - Pytest test suite
- `.env.template` - Example environment configuration values

## Recommended Workflow
1. **Install dependencies**
   ```bash
   ./setup.sh
   ```
   This script installs Python (via Poetry) and Node requirements.

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
   poetry run uvicorn app.main:app --reload
   ```

Keep commits focused and run the commands above to ensure code quality.
