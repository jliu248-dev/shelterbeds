"""Shared test setup: a fresh in-memory database per test, plus helper fixtures.

Requests from the test client run with no app context left open, the same as a
real server. (If one stayed open, Flask-Login would reuse the first logged-in user
for every later request in the test.) Fixtures that touch the database open a
short app context themselves and hand back plain ids.
"""
import pytest

from app import create_app
from app.extensions import db
from app.models import BedType, Hold, Role, Shelter, Status, User
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


def _add(app, obj):
    with app.app_context():
        db.session.add(obj)
        db.session.commit()
        return obj.id


@pytest.fixture
def make_user(app):
    """make_user(email, role=..., shelter_id=...) -> new approved user's id."""
    def _make(email, role=Role.SEEKER, shelter_id=None):
        user = User(email=email, role=role, status=Status.APPROVED, shelter_id=shelter_id)
        user.set_password("password123")
        return _add(app, user)
    return _make


@pytest.fixture
def shelter_id(app):
    return _add(app, Shelter(name="Hope House", address="1 Main St", city="San Jose"))


@pytest.fixture
def other_shelter_id(app):
    return _add(app, Shelter(name="Second Street Shelter", address="2 Second St", city="San Jose"))


@pytest.fixture
def bed_type_id(app, shelter_id):
    return _add(app, BedType(shelter_id=shelter_id, label="Men 18+", total=5, available=2))


@pytest.fixture
def client_for(app):
    """client_for(user_id) -> a test client already logged in as that user."""
    def _client(user_id):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user_id)  # how Flask-Login remembers who is logged in
            sess["_fresh"] = True
        return client
    return _client


# --- Read the database after a request ---

@pytest.fixture
def available(app):
    """available(bed_type_id) -> current open beds."""
    def _available(bed_type_id):
        with app.app_context():
            return db.session.get(BedType, bed_type_id).available
    return _available


@pytest.fixture
def holds(app):
    """holds() -> list of (id, user_id, status) for every hold."""
    def _holds():
        with app.app_context():
            return [(h.id, h.user_id, h.status) for h in Hold.query.order_by(Hold.id)]
    return _holds
