# Football Auth Demo

## Setup

1. `poetry install`
2. `npm install tailwindcss`
3. `npm run build:css`
4. `poetry run uvicorn app.main:app --reload`
5. Adjust settings in `config.ini` if your Cognito details differ.

Visit `http://localhost:8000/auth/login` to view the login form. Incorrect credentials should display an error in place without page reload; correct credentials redirect back to home.
