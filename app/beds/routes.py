from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.beds import bp
from app.beds.forms import BedCountsForm, BedTypeForm
from app.decorators import approved_required, role_required
from app.extensions import db
from app.models import BedType, Hold, HoldStatus, Role, Shelter


def _get_or_404(model, obj_id):
    obj = db.session.get(model, obj_id)
    if obj is None:
        abort(404)
    return obj


def _require_can_manage(shelter):
    """Admins can manage any shelter's beds; approved staff only their own."""
    if not shelter.can_be_edited_by(current_user):
        abort(403)


def _active_hold_counts(bed_type_ids):
    """{bed_type_id: number of active holds} for the given bed groups."""
    if not bed_type_ids:
        return {}
    rows = (
        db.session.query(Hold.bed_type_id, func.count(Hold.id))
        .filter(Hold.bed_type_id.in_(bed_type_ids), Hold.status == HoldStatus.ACTIVE)
        .group_by(Hold.bed_type_id)
        .all()
    )
    return dict(rows)


# --- Browse: any approved user. ---

@bp.route("/")
@approved_required
def index():
    shelters = (
        Shelter.query.options(selectinload(Shelter.bed_types))
        .order_by(Shelter.city.desc(), Shelter.name)
        .all()
    )
    return render_template("beds/index.html", shelters=shelters)


# --- Manage: shelter staff (own shelter) and admins (any shelter). ---

@bp.route("/manage")
@role_required(Role.SHELTER_STAFF, Role.ADMIN)
def manage_home():
    if current_user.is_admin:
        # Admins pick a shelter from the Beds page.
        return redirect(url_for("beds.index"))
    if not current_user.shelter_id:
        flash("Your account isn't linked to a shelter yet. Ask an admin to link it.", "warning")
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("beds.manage", shelter_id=current_user.shelter_id))


@bp.route("/manage/<int:shelter_id>")
@role_required(Role.SHELTER_STAFF, Role.ADMIN)
def manage(shelter_id):
    shelter = _get_or_404(Shelter, shelter_id)
    _require_can_manage(shelter)
    return _render_manage(shelter)


def _render_manage(shelter, add_form=None, failed_form=None, failed_id=None, status=200):
    """Render the manage page. If a form failed validation, show it with its errors."""
    bed_types = sorted(shelter.bed_types, key=lambda b: b.label.lower())
    count_forms = {}
    for b in bed_types:
        if b.id == failed_id:
            count_forms[b.id] = failed_form
        else:
            # formdata=None so these forms show saved values, not another form's POST data.
            count_forms[b.id] = BedCountsForm(formdata=None, obj=b, prefix=f"b{b.id}")
    return render_template(
        "beds/manage.html",
        shelter=shelter,
        bed_types=bed_types,
        count_forms=count_forms,
        hold_counts=_active_hold_counts([b.id for b in bed_types]),
        add_form=add_form or BedTypeForm(formdata=None, prefix="new"),
    ), status


@bp.route("/manage/<int:shelter_id>/add", methods=["POST"])
@role_required(Role.SHELTER_STAFF, Role.ADMIN)
def add_bed_type(shelter_id):
    shelter = _get_or_404(Shelter, shelter_id)
    _require_can_manage(shelter)

    form = BedTypeForm(prefix="new")
    if form.validate_on_submit():
        label = form.label.data.strip()
        taken = any(b.label.lower() == label.lower() for b in shelter.bed_types)
        if taken:
            form.label.errors.append("This shelter already has a bed group with that name.")
        else:
            db.session.add(BedType(shelter=shelter, label=label,
                                   total=form.total.data, available=form.available.data))
            db.session.commit()
            flash(f"Added bed group “{label}”.", "success")
            return redirect(url_for("beds.manage", shelter_id=shelter.id))

    return _render_manage(shelter, add_form=form, status=400)


@bp.route("/types/<int:bed_type_id>/update", methods=["POST"])
@role_required(Role.SHELTER_STAFF, Role.ADMIN)
def update_bed_type(bed_type_id):
    bed_type = _get_or_404(BedType, bed_type_id)
    shelter = bed_type.shelter
    _require_can_manage(shelter)

    form = BedCountsForm(prefix=f"b{bed_type.id}")
    if form.validate_on_submit():
        on_hold = _active_hold_counts([bed_type.id]).get(bed_type.id, 0)
        if form.total.data < form.available.data + on_hold:
            form.total.errors.append(
                f"Total must cover open beds plus the {on_hold} on hold "
                f"(at least {form.available.data + on_hold}).")
        else:
            bed_type.total = form.total.data
            bed_type.available = form.available.data
            db.session.commit()
            flash(f"Updated “{bed_type.label}”.", "success")
            return redirect(url_for("beds.manage", shelter_id=shelter.id))

    return _render_manage(shelter, failed_form=form, failed_id=bed_type.id, status=400)


@bp.route("/types/<int:bed_type_id>/delete", methods=["POST"])
@role_required(Role.SHELTER_STAFF, Role.ADMIN)
def delete_bed_type(bed_type_id):
    bed_type = _get_or_404(BedType, bed_type_id)
    shelter = bed_type.shelter
    _require_can_manage(shelter)

    if _active_hold_counts([bed_type.id]).get(bed_type.id, 0):
        flash(f"“{bed_type.label}” has active holds. Wait for them to finish before deleting.", "danger")
        return redirect(url_for("beds.manage", shelter_id=shelter.id))

    label = bed_type.label
    db.session.delete(bed_type)
    db.session.commit()
    flash(f"Deleted bed group “{label}”.", "info")
    return redirect(url_for("beds.manage", shelter_id=shelter.id))
