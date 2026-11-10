from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class Role:
    ADMIN = "admin"
    SHELTER_STAFF = "shelter_staff"
    SEEKER = "seeker"

    ALL = (ADMIN, SHELTER_STAFF, SEEKER)
    # Roles a person may pick for themselves on the register page.
    SELF_REGISTER = (SEEKER, SHELTER_STAFF)


class Status:
    PENDING = "pending"
    APPROVED = "approved"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.SEEKER)
    status = db.Column(db.String(20), nullable=False, default=Status.PENDING)
    # Which shelter a staff member works at (empty for seekers and admins).
    shelter_id = db.Column(db.Integer, db.ForeignKey("shelters.id"), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    shelter = db.relationship("Shelter", back_populates="staff")
    reviews = db.relationship("Review", back_populates="author", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_approved(self):
        return self.status == Status.APPROVED

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    def has_role(self, *roles):
        return self.role in roles

    @property
    def role_label(self):
        return self.role.replace("_", " ").title()

    def __repr__(self):
        return f"<User {self.email} ({self.role}, {self.status})>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
