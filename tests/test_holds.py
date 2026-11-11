"""Tests for the holds workflow: place, cancel, confirm, expire."""
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import BedType, Hold, HoldStatus, Role


def place(client, bed_type_id):
    return client.post(f"/beds/types/{bed_type_id}/hold")


def only_hold(holds):
    [hold] = holds()
    return hold  # (id, user_id, status)


# --- Placing a hold ---

def test_placing_a_hold_decrements_available(make_user, client_for, bed_type_id, available, holds):
    seeker = make_user("seeker@example.com")

    resp = place(client_for(seeker), bed_type_id)

    assert resp.status_code == 302
    assert available(bed_type_id) == 1
    assert only_hold(holds)[1:] == (seeker, HoldStatus.ACTIVE)


def test_cannot_hold_when_no_beds_are_available(app, make_user, client_for, bed_type_id, available, holds):
    with app.app_context():
        db.session.get(BedType, bed_type_id).available = 0
        db.session.commit()
    seeker = make_user("seeker@example.com")

    resp = place(client_for(seeker), bed_type_id)

    assert resp.status_code == 302  # back to the beds page with an error message
    assert holds() == []
    assert available(bed_type_id) == 0


def test_only_one_active_hold_per_seeker(make_user, client_for, bed_type_id, available, holds):
    client = client_for(make_user("seeker@example.com"))

    place(client, bed_type_id)
    place(client, bed_type_id)

    assert len(holds()) == 1
    assert available(bed_type_id) == 1


# --- Ownership ---

def test_second_seeker_cannot_see_or_cancel_first_seekers_hold(
        make_user, client_for, bed_type_id, available, holds):
    first = client_for(make_user("first@example.com"))
    second = client_for(make_user("second@example.com"))
    place(first, bed_type_id)
    hold_id = only_hold(holds)[0]

    assert "Hope House" in first.get("/beds/holds").get_data(as_text=True)
    assert "Hope House" not in second.get("/beds/holds").get_data(as_text=True)

    assert second.post(f"/beds/holds/{hold_id}/cancel").status_code == 403
    assert only_hold(holds)[2] == HoldStatus.ACTIVE
    assert available(bed_type_id) == 1


def test_staff_from_another_shelter_cannot_confirm(
        make_user, client_for, bed_type_id, other_shelter_id, holds):
    place(client_for(make_user("seeker@example.com")), bed_type_id)
    hold_id = only_hold(holds)[0]
    outsider = make_user("staff@other.org", role=Role.SHELTER_STAFF, shelter_id=other_shelter_id)

    resp = client_for(outsider).post(f"/beds/holds/{hold_id}/confirm")

    assert resp.status_code == 403
    assert only_hold(holds)[2] == HoldStatus.ACTIVE


def test_own_staff_can_confirm_and_bed_stays_taken(
        make_user, client_for, bed_type_id, shelter_id, available, holds):
    place(client_for(make_user("seeker@example.com")), bed_type_id)
    hold_id = only_hold(holds)[0]
    staff = make_user("staff@hope.org", role=Role.SHELTER_STAFF, shelter_id=shelter_id)

    resp = client_for(staff).post(f"/beds/holds/{hold_id}/confirm")

    assert resp.status_code == 302
    assert only_hold(holds)[2] == HoldStatus.CONFIRMED
    assert available(bed_type_id) == 1


def test_missing_hold_returns_404(make_user, client_for):
    seeker = client_for(make_user("seeker@example.com"))
    assert seeker.post("/beds/holds/9999/cancel").status_code == 404


# --- Releasing the bed ---

def test_cancel_returns_the_bed(make_user, client_for, bed_type_id, available, holds):
    client = client_for(make_user("seeker@example.com"))
    place(client, bed_type_id)
    hold_id = only_hold(holds)[0]
    assert available(bed_type_id) == 1

    client.post(f"/beds/holds/{hold_id}/cancel")

    assert only_hold(holds)[2] == HoldStatus.CANCELLED
    assert available(bed_type_id) == 2


def test_cancelled_hold_cannot_be_cancelled_again(make_user, client_for, bed_type_id, available, holds):
    client = client_for(make_user("seeker@example.com"))
    place(client, bed_type_id)
    hold_id = only_hold(holds)[0]

    client.post(f"/beds/holds/{hold_id}/cancel")
    client.post(f"/beds/holds/{hold_id}/cancel")

    assert available(bed_type_id) == 2  # released once, not twice


def test_expired_hold_returns_the_bed(app, make_user, client_for, bed_type_id, available, holds):
    client = client_for(make_user("seeker@example.com"))
    place(client, bed_type_id)
    hold_id = only_hold(holds)[0]
    assert available(bed_type_id) == 1

    # Pretend the 60 minutes have passed.
    with app.app_context():
        db.session.get(Hold, hold_id).expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.session.commit()

    # Any beds request runs expire_stale_holds() first.
    client.get("/beds/")

    assert only_hold(holds)[2] == HoldStatus.EXPIRED
    assert available(bed_type_id) == 2
