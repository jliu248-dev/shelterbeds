from flask import (abort, current_app, flash, redirect, render_template,
                   send_from_directory, url_for)
from flask_login import current_user
from sqlalchemy.orm import selectinload

from app.decorators import approved_required, login_required, role_required
from app.extensions import db
from app.models import Review, Role, Shelter
from app.shelters import bp
from app.shelters.forms import ReviewForm, ShelterEditForm
from app.shelters.photos import delete_photo, save_photo


def _get_shelter_or_404(shelter_id):
    shelter = db.session.get(Shelter, shelter_id)
    if shelter is None:
        abort(404)
    return shelter


# --- Public pages: anyone can browse shelters without an account. ---

@bp.route("/")
def index():
    shelters = (
        Shelter.query.options(selectinload(Shelter.reviews))
        .order_by(Shelter.city.desc(), Shelter.name)  # Santa Clara first, then San Jose
        .all()
    )
    return render_template("shelters/index.html", shelters=shelters)


@bp.route("/<int:shelter_id>")
def detail(shelter_id):
    shelter = _get_shelter_or_404(shelter_id)
    form = None
    my_review = None
    if current_user.is_authenticated:
        my_review = next((r for r in shelter.reviews if r.user_id == current_user.id), None)
        if _can_review() and my_review is None:
            form = ReviewForm()
    return render_template("shelters/detail.html", shelter=shelter, form=form,
                           my_review=my_review, can_review=_can_review())


@bp.route("/<int:shelter_id>/photo")
def photo(shelter_id):
    shelter = _get_shelter_or_404(shelter_id)
    if not shelter.photo_filename:
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], shelter.photo_filename)


# --- Reviews: approved seekers only. ---

def _can_review():
    return (current_user.is_authenticated and current_user.is_approved
            and current_user.role == Role.SEEKER)


@bp.route("/<int:shelter_id>/reviews", methods=["POST"])
@role_required(Role.SEEKER)
def add_review(shelter_id):
    shelter = _get_shelter_or_404(shelter_id)
    if Review.query.filter_by(shelter_id=shelter.id, user_id=current_user.id).first():
        flash("You've already reviewed this shelter. Delete your review to write a new one.", "warning")
        return redirect(url_for("shelters.detail", shelter_id=shelter.id))

    form = ReviewForm()
    if form.validate_on_submit():
        db.session.add(Review(shelter=shelter, author=current_user,
                              rating=int(form.rating.data), body=form.body.data.strip()))
        db.session.commit()
        flash("Thanks! Your review is posted.", "success")
        return redirect(url_for("shelters.detail", shelter_id=shelter.id) + "#reviews")

    # Show the page again with the form errors.
    return render_template("shelters/detail.html", shelter=shelter, form=form,
                           my_review=None, can_review=True), 400


@bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = db.session.get(Review, review_id)
    if review is None:
        abort(404)
    if not review.can_be_deleted_by(current_user):
        abort(403)
    shelter_id = review.shelter_id
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.", "info")
    return redirect(url_for("shelters.detail", shelter_id=shelter_id) + "#reviews")


# --- Editing: admins, or approved staff of that shelter. ---

@bp.route("/<int:shelter_id>/edit", methods=["GET", "POST"])
@approved_required
def edit(shelter_id):
    shelter = _get_shelter_or_404(shelter_id)
    if not shelter.can_be_edited_by(current_user):
        abort(403)

    form = ShelterEditForm(obj=shelter)
    if form.validate_on_submit():
        for field in ("name", "operator", "address", "city", "zip_code",
                      "serves", "description", "website"):
            value = (getattr(form, field).data or "").strip() or None
            setattr(shelter, field, value)

        if form.photo.data:
            filename = save_photo(form.photo.data)
            if filename is None:
                flash("That file doesn't look like a JPG, PNG or WebP image.", "danger")
                return render_template("shelters/edit.html", shelter=shelter, form=form), 400
            delete_photo(shelter.photo_filename)
            shelter.photo_filename = filename
        elif form.remove_photo.data:
            delete_photo(shelter.photo_filename)
            shelter.photo_filename = None

        db.session.commit()
        flash("Shelter updated.", "success")
        return redirect(url_for("shelters.detail", shelter_id=shelter.id))

    return render_template("shelters/edit.html", shelter=shelter, form=form)
