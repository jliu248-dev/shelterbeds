from flask import render_template
from sqlalchemy.orm import selectinload

from app.beds import bp
from app.decorators import approved_required
from app.models import Shelter


# Placeholder for now: lists each shelter with its bed groups.
# Coming next: staff page to update counts (step 4), search and holds (step 5),
# automatic hold expiration (step 6).

@bp.route("/")
@approved_required
def index():
    shelters = (
        Shelter.query.options(selectinload(Shelter.bed_types))
        .order_by(Shelter.city.desc(), Shelter.name)
        .all()
    )
    return render_template("beds/index.html", shelters=shelters)
