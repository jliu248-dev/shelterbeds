"""Entry point used by `flask` commands and by gunicorn (`gunicorn wsgi:app`)."""
from app import create_app

app = create_app()
