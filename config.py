"""App settings, read from environment variables (and a local .env file)."""
import os

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load .env for local development. On Cloud Run, real env vars are used instead.
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Local fallback: a SQLite file in the instance/ folder (git-ignored).
        os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
        return "sqlite:///" + os.path.join(BASE_DIR, "instance", "shelterbeds.db")
    # Some hosts hand out "postgres://", which SQLAlchemy no longer accepts.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    APP_ENV = os.environ.get("APP_ENV", "development")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploaded shelter photos. Note: on Cloud Run this disk is temporary;
    # switch to Google Cloud Storage before relying on uploads in production.
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "instance", "uploads"))
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB per request

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Only send cookies over HTTPS in production (Cloud Run is always HTTPS).
    SESSION_COOKIE_SECURE = APP_ENV == "production"
    REMEMBER_COOKIE_SECURE = APP_ENV == "production"


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
