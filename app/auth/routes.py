from urllib.parse import urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.auth import bp
from app.auth.forms import LoginForm, RegisterForm
from app.decorators import login_required
from app.extensions import db
from app.models import Role, Status, User


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return render_template("auth/register.html", form=form)

        role = form.role.data
        if role not in Role.SELF_REGISTER:  # defense in depth; the form already checks
            flash("Invalid role.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            email=email,
            role=role,
            # Seekers can use the app right away; shelter staff wait for an admin.
            status=Status.APPROVED if role == Role.SEEKER else Status.PENDING,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        if user.is_approved:
            flash("Account created. You can log in now.", "success")
        else:
            flash("Account created. An admin must approve it before you can manage beds.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember.data)
        flash("Logged in.", "success")
        return redirect(_safe_next_url() or url_for("main.dashboard"))

    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))


def _safe_next_url():
    """Only allow redirects to paths on this site (blocks open redirects)."""
    target = request.args.get("next", "")
    parts = urlsplit(target)
    if target.startswith("/") and not target.startswith("//") and not parts.netloc and not parts.scheme:
        return target
    return None
