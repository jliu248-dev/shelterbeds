from flask import abort, flash, redirect, render_template, request, url_for

from app.admin import bp
from app.decorators import role_required
from app.extensions import db
from app.models import Role, Shelter, Status, User


@bp.route("/approvals")
@role_required(Role.ADMIN)
def approvals():
    pending = (
        User.query.filter_by(role=Role.SHELTER_STAFF, status=Status.PENDING)
        .order_by(User.created_at)
        .all()
    )
    shelters = Shelter.query.order_by(Shelter.name).all()
    return render_template("admin/approvals.html", pending=pending, shelters=shelters)


@bp.route("/users/<int:user_id>/approve", methods=["POST"])
@role_required(Role.ADMIN)
def approve_user(user_id):
    user = db.session.get(User, user_id)
    if user is None or user.role != Role.SHELTER_STAFF or user.status != Status.PENDING:
        abort(404)

    # Optionally link the staff member to the shelter they work at.
    shelter_id = request.form.get("shelter_id", type=int)
    if shelter_id:
        shelter = db.session.get(Shelter, shelter_id)
        if shelter is None:
            abort(400)
        user.shelter = shelter

    user.status = Status.APPROVED
    db.session.commit()
    where = f" for {user.shelter.name}" if user.shelter else ""
    flash(f"Approved {user.email}{where}.", "success")
    return redirect(url_for("admin.approvals"))
