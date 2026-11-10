"""Create the first admin account.

Reads ADMIN_EMAIL and ADMIN_PASSWORD from the environment (or .env).
Does nothing if a user with that email already exists.

    python seed_admin.py
"""
import os
import sys

from app import create_app
from app.extensions import db
from app.models import Role, Status, User


def main():
    app = create_app()  # also loads .env via config.py
    email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD") or ""

    if not email or not password:
        sys.exit("Error: set ADMIN_EMAIL and ADMIN_PASSWORD first.")
    if len(password) < 8:
        sys.exit("Error: ADMIN_PASSWORD must be at least 8 characters.")

    with app.app_context():
        if User.query.filter_by(email=email).first():
            print(f"User {email} already exists. Skipping.")
            return

        admin = User(email=email, role=Role.ADMIN, status=Status.APPROVED)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin {email}.")


if __name__ == "__main__":
    main()
