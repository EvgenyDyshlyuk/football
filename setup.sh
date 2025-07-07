#!/usr/bin/env bash
set -e
set -x

MARKER_FILE=".env_setup_done"

if [ -f "$MARKER_FILE" ]; then
  echo "Environment already configured. Remove $MARKER_FILE to re-run."
  exit 0
fi

echo "=== Configuring Python & Poetry ==="

# Ensure Poetry is installed
if ! command -v poetry >/dev/null 2>&1; then
  echo "Poetry not found. Installing via official installer…"
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
fi

# Pick Python interpreter: prefer pyenv, else system python3
if command -v pyenv >/dev/null 2>&1; then
  echo "pyenv detected → installing/using Python 3.13.5"
  pyenv install -s 3.13.3
  pyenv local 3.13.3
  PYTHON_PATH="$(pyenv which python)"
else
  echo "pyenv not found → falling back to system python3"
  PYTHON_PATH="$(command -v python3)"
fi

# Point Poetry at the interpreter & keep venv in-project
poetry config virtualenvs.in-project true
poetry env use "$PYTHON_PATH"

# Initialize pyproject.toml if missing
if [ ! -f pyproject.toml ]; then
  poetry init --name yard-football-manager \
    --python "^3.13" \
    --dependency fastapi=0.115.14 \
    --dependency "uvicorn[standard]=0.35.0" \
    --dependency jinja2=3.1.6 \
    --dependency pydantic=2.11.7 \
    --dependency python-multipart=0.0.20 \
    -n
fi

# Install all Python deps
poetry install

echo "=== Configuring Node & npm ==="

# Install nvm if needed
if ! command -v nvm >/dev/null 2>&1; then
  echo "nvm not found. Bootstrapping nvm…"
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
fi

# Make sure nvm is loaded
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Install & select Node
nvm install 22.17.0
nvm use 22.17.0
nvm alias default 22.17.0

# Init npm if needed
if [ ! -f package.json ]; then
  npm init -y
fi

# Your CSS toolchain + front-end libs
npm install -D tailwindcss@4.0.0 postcss@8.4.27 autoprefixer@10.4.14
npm install htmx.org@2.0.6 alpinejs@3.14.9

# Tailwind config
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

# Helper npm scripts
npm pkg set scripts.build:css="tailwindcss -i ./app/static/css/input.css -o ./app/static/css/tailwind.css"
npm pkg set scripts.watch:css="tailwindcss -i ./app/static/css/input.css -o ./app/static/css/tailwind.css --watch"

# Mark complete
touch "$MARKER_FILE"
echo "Environment setup complete."
