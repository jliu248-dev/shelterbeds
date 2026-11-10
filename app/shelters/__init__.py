from flask import Blueprint

bp = Blueprint("shelters", __name__)

from app.shelters import routes  # noqa: E402,F401
