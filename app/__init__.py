"""Application factory.

create_app() builds and returns a configured Flask app. To add a feature,
create a blueprint package under app/ and register it in register_blueprints().
"""
from flask import Flask

from config import Config
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    _check_secret_key(app)

    # Attach extensions to this app.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import models so SQLAlchemy and Flask-Migrate know about every table.
    from app import models  # noqa: F401

    register_blueprints(app)

    from app.errors import register_error_handlers
    register_error_handlers(app)

    from app.filters import register_filters
    register_filters(app)

    return app


def register_blueprints(app):
    from app.main import bp as main_bp
    from app.auth import bp as auth_bp
    from app.admin import bp as admin_bp
    from app.shelters import bp as shelters_bp
    from app.beds import bp as beds_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(shelters_bp, url_prefix="/shelters")
    app.register_blueprint(beds_bp, url_prefix="/beds")

    # Teammates: register new blueprints here.


def _check_secret_key(app):
    if app.config.get("SECRET_KEY"):
        return
    if app.config.get("APP_ENV") == "production":
        raise RuntimeError("SECRET_KEY must be set in production.")
    # Local development only: a throwaway key so the app still starts.
    app.logger.warning("SECRET_KEY not set; using an insecure development key.")
    app.config["SECRET_KEY"] = "dev-insecure-key-change-me"
