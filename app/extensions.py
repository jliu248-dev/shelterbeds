"""Flask extension objects.

They are created here without an app and attached to the app inside
create_app(). Import them from here anywhere you need them, e.g.
    from app.extensions import db
"""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import MetaData

# Consistent constraint names, so migrations can alter tables (needed on SQLite).
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Where @login_required sends people who aren't logged in.
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to see that page."
login_manager.login_message_category = "info"
