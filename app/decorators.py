"""Reusable access-control decorators. All checks run on the server.

Usage (put the route decorator first):

    @bp.route("/beds/new")
    @role_required(Role.SHELTER_STAFF)
    def new_bed(): ...

- login_required:     must be logged in.
- approved_required:  must be logged in AND approved by an admin.
- role_required(...): must be logged in, approved, AND have one of the roles.
"""
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user
from flask_login import login_required as _flask_login_required

# Re-exported so every access check can be imported from one place.
login_required = _flask_login_required


def approved_required(view):
    @wraps(view)
    @_flask_login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_approved:
            flash("Your account is waiting for admin approval.", "warning")
            return redirect(url_for("main.dashboard"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @approved_required
        def wrapped(*args, **kwargs):
            if not current_user.has_role(*roles):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
