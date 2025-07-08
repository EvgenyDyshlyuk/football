# Football Auth Demo

## Setup

1. Clone the repository:
   ```bash
   git clone
run setup.sh
(poetry will be run according to the setup.sh script)
Adjust settings in `config.ini` if your Cognito details differ.

## Testing
poetry run pytest
poetry run ruff check .

## Running the Application
poetry run uvicorn app.main:app --reload