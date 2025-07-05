#!/usr/bin/env bash
set -e
set -x

MARKER_FILE=".env_setup_done"

if [ -f "$MARKER_FILE" ]; then
  echo "Environment already configured. Remove $MARKER_FILE to re-run."
  exit 0
fi

echo "Checking for required tools..."

if ! command -v pyenv >/dev/null 2>&1; then
  echo "pyenv is not installed. Please install pyenv from https://github.com/pyenv/pyenv and re-run this script."
  exit 1
fi

if ! command -v poetry >/dev/null 2>&1; then
  echo "Poetry not found. Installing..."
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v nvm >/dev/null 2>&1; then
  echo "nvm not found. Installing..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
fi

# Ensure nvm is loaded
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Setup Python via pyenv
pyenv install -s 3.13.5
pyenv local 3.13.5

# Configure Poetry
poetry config virtualenvs.in-project true
poetry env use "$(pyenv which python)"

if [ ! -f pyproject.toml ]; then
  poetry init --name yard-football-manager \
    --python "^3.13" \
    --dependency fastapi=0.115.14 \
    --dependency 'uvicorn[standard]=0.35.0' \
    --dependency jinja2=3.1.6 \
    --dependency pydantic=2.11.7 \
    --dependency python-multipart=0.0.20 \
    -n
fi

poetry install

# Setup Node.js via nvm
nvm install 22.17.0
nvm use 22.17.0
nvm alias default 22.17.0

if [ ! -f package.json ]; then
  npm init -y
fi

npm install -D tailwindcss@4.0.0 postcss@8.4.27 autoprefixer@10.4.14
npm install htmx.org@2.0.6 alpinejs@3.14.9

if [ ! -f tailwind.config.js ]; then
  cat > tailwind.config.js <<'TAILWIND'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html"],
  theme: { extend: {} },
  plugins: [],
}
TAILWIND
fi

npm pkg set scripts.build:css="tailwindcss -i ./app/static/css/input.css -o ./app/static/css/tailwind.css"
npm pkg set scripts.watch:css="tailwindcss -i ./app/static/css/input.css -o ./app/static/css/tailwind.css --watch"

touch "$MARKER_FILE"

echo "Environment setup complete."
