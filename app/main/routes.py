from flask import render_template
from sqlalchemy.orm import selectinload

from app.decorators import login_required
from app.main import bp
from app.models import Shelter


@bp.route("/")
def index():
    featured = (
        Shelter.query.options(selectinload(Shelter.reviews))
        .order_by(Shelter.city.desc(), Shelter.name)
        .limit(3)
        .all()
    )
    return render_template("main/index.html", featured=featured,
                           shelter_count=Shelter.query.count())


@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("main/dashboard.html")
