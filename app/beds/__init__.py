from flask import Blueprint

bp = Blueprint("beds", __name__)

from app.beds import routes  # noqa: E402,F401
