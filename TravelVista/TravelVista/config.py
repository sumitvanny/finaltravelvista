"""
config.py
Central configuration for TravelVista.
Reads sensitive values from environment variables (.env) so nothing
secret is hard-coded into source control.
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def _bool(env_val, default=False):
    if env_val is None:
        return default
    return str(env_val).lower() in ("1", "true", "yes", "on")


class Config:
    # --- Core Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this-in-production")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # --- Database ---
    # Defaults to SQLite for local development. Swap the DATABASE_URL env
    # var for a MySQL/PostgreSQL URI in production, e.g.:
    #   postgresql://user:password@localhost:5432/travelvista
    #   mysql+pymysql://user:password@localhost:3306/travelvista
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        "sqlite:///" + os.path.join(basedir, "instance", "database.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Sessions / cookies ---
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool(os.environ.get("SESSION_COOKIE_SECURE"), default=False)

    # --- File uploads ---
    UPLOAD_FOLDER = os.path.join(basedir, "static", "images", "uploads")
    DESTINATION_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "destinations")
    PROFILE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "profiles")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB max upload

    # --- Mail (used for password reset emails; console-backed by default) ---
    MAIL_BACKEND = os.environ.get("MAIL_BACKEND", "console")  # "console" or "smtp"
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = _bool(os.environ.get("MAIL_USE_TLS"), default=True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@travelvista.com")

    # --- App-specific ---
    APP_NAME = "TravelVista"
    ITEMS_PER_PAGE = 9
    ADMIN_ITEMS_PER_PAGE = 15


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
