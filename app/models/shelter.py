from datetime import datetime, timezone

from app.extensions import db


def _now():
    return datetime.now(timezone.utc)


class Shelter(db.Model):
    __tablename__ = "shelters"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    operator = db.Column(db.String(150))          # organization that runs it
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    zip_code = db.Column(db.String(10))
    serves = db.Column(db.String(150))            # short label, e.g. "Men 18+"
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    photo_filename = db.Column(db.String(255))    # uploaded photo in instance/uploads
    # When the listing details were last checked against a public source.
    info_checked_on = db.Column(db.Date)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    reviews = db.relationship(
        "Review", back_populates="shelter", cascade="all, delete-orphan",
        order_by="Review.created_at.desc()",
    )
    staff = db.relationship("User", back_populates="shelter")

    @property
    def full_address(self):
        parts = [self.address, self.city, "CA"]
        line = ", ".join(parts)
        return f"{line} {self.zip_code}" if self.zip_code else line

    @property
    def review_count(self):
        return len(self.reviews)

    @property
    def average_rating(self):
        if not self.reviews:
            return None
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    def can_be_edited_by(self, user):
        """Admins can edit any shelter; approved staff only their own."""
        if not user.is_authenticated or not user.is_approved:
            return False
        return user.is_admin or (user.role == "shelter_staff" and user.shelter_id == self.id)

    def __repr__(self):
        return f"<Shelter {self.name}>"


class Review(db.Model):
    __tablename__ = "reviews"
    # One review per person per shelter.
    __table_args__ = (db.UniqueConstraint("shelter_id", "user_id", name="uq_reviews_shelter_user"),)

    id = db.Column(db.Integer, primary_key=True)
    shelter_id = db.Column(db.Integer, db.ForeignKey("shelters.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    shelter = db.relationship("Shelter", back_populates="reviews")
    author = db.relationship("User", back_populates="reviews")

    def can_be_deleted_by(self, user):
        return user.is_authenticated and (user.is_admin or user.id == self.user_id)
