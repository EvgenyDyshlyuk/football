"""Jinja2 environment configuration for HTML templates."""

from pathlib import Path
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
