from datetime import datetime, timedelta, timezone

from app.extensions import db

# How long a hold lasts before it expires and the bed is released.
HOLD_MINUTES = 60


def _now():
    return datetime.now(timezone.utc)


def _hold_expiry():
    return _now() + timedelta(minutes=HOLD_MINUTES)


class HoldStatus:
    ACTIVE = "active"
    CONFIRMED = "confirmed"   # person checked in at the shelter
    EXPIRED = "expired"
    CANCELLED = "cancelled"

    ALL = (ACTIVE, CONFIRMED, EXPIRED, CANCELLED)


class BedType(db.Model):
    """A group of beds at one shelter, e.g. "Men 18+" with 40 total, 3 open."""

    __tablename__ = "bed_types"

    id = db.Column(db.Integer, primary_key=True)
    shelter_id = db.Column(db.Integer, db.ForeignKey("shelters.id"), nullable=False, index=True)
    label = db.Column(db.String(80), nullable=False)
    total = db.Column(db.Integer, nullable=False, default=0)
    available = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    shelter = db.relationship("Shelter", backref=db.backref("bed_types", cascade="all, delete-orphan"))
    holds = db.relationship("Hold", back_populates="bed_type", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("shelter_id", "label", name="uq_bed_types_shelter_id_label"),
        db.CheckConstraint("total >= 0", name="total_nonneg"),
        db.CheckConstraint("available >= 0 AND available <= total", name="available_range"),
    )

    def __repr__(self):
        return f"<BedType {self.label} {self.available}/{self.total}>"


class Hold(db.Model):
    """A temporary reservation of one bed for one person."""

    __tablename__ = "holds"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    bed_type_id = db.Column(db.Integer, db.ForeignKey("bed_types.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default=HoldStatus.ACTIVE, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_hold_expiry)

    user = db.relationship("User", backref="holds")
    bed_type = db.relationship("BedType", back_populates="holds")

    @property
    def is_active(self):
        return self.status == HoldStatus.ACTIVE

    def __repr__(self):
        return f"<Hold {self.id} user={self.user_id} bed_type={self.bed_type_id} {self.status}>"
