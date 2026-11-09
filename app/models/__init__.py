"""All database models.

Import every model here so Flask-Migrate can find it when generating migrations.
Teammates: add a new file (e.g. bed.py) and import its model below.
"""
from app.models.user import Role, Status, User  # noqa: F401
from app.models.shelter import Review, Shelter  # noqa: F401
