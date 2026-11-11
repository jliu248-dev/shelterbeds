"""Hold workflow: place, cancel, confirm, and expire holds.

Every change to a hold's status or a bed count is a conditional SQL UPDATE
("... WHERE status = 'active'", "... WHERE available > 0"). The database applies
each one atomically, so two requests racing for the same bed or the same hold
can't both succeed. We check the row count to see whether ours won.

Routes do the access checks (role, ownership) and then call these functions.
"""
from datetime import datetime, timezone

from sqlalchemy import case, select, update

from app.extensions import db
from app.models import BedType, Hold, HoldStatus, User


class HoldError(Exception):
    """A hold action that isn't allowed right now. The message is safe to show the user."""


def _now():
    return datetime.now(timezone.utc)


def _take_bed(bed_type_id):
    """Take one open bed. Returns False if none were left."""
    result = db.session.execute(
        update(BedType)
        .where(BedType.id == bed_type_id, BedType.available > 0)
        .values(available=BedType.available - 1)
    )
    return result.rowcount == 1


def _release_bed(bed_type_id):
    """Put one bed back. Capped at total so a staff edit can't push us past the limit."""
    db.session.execute(
        update(BedType)
        .where(BedType.id == bed_type_id)
        .values(available=case(
            (BedType.available < BedType.total, BedType.available + 1),
            else_=BedType.available,
        ))
    )


def _change_status(hold_id, new_status):
    """Move a hold from active to new_status. Returns False if it wasn't active anymore."""
    result = db.session.execute(
        update(Hold)
        .where(Hold.id == hold_id, Hold.status == HoldStatus.ACTIVE)
        .values(status=new_status)
    )
    return result.rowcount == 1


def expire_stale_holds():
    """Expire every active hold past its expiry time and release its bed. One transaction.

    Cloud Run has no background worker, so the beds blueprint calls this at the
    start of each request instead of on a timer.
    """
    stale = db.session.execute(
        select(Hold.id, Hold.bed_type_id)
        .where(Hold.status == HoldStatus.ACTIVE, Hold.expires_at <= _now())
    ).all()
    if not stale:
        return 0

    expired = 0
    for hold_id, bed_type_id in stale:
        # If another request expired this hold first, skip it so the bed isn't released twice.
        if _change_status(hold_id, HoldStatus.EXPIRED):
            _release_bed(bed_type_id)
            expired += 1
    db.session.commit()
    return expired


def active_hold_for(user):
    """The user's current active hold, or None."""
    return Hold.query.filter_by(user_id=user.id, status=HoldStatus.ACTIVE).first()


def place_hold(user, bed_type):
    """Hold one bed in bed_type for user. Raises HoldError if not allowed."""
    # Lock the user's row so two clicks at once can't both create a hold
    # (Postgres row lock; SQLite ignores it and runs writes one at a time).
    db.session.execute(select(User.id).where(User.id == user.id).with_for_update())

    if active_hold_for(user):
        db.session.rollback()
        raise HoldError("You already have an active hold. Cancel it before holding another bed.")

    if not _take_bed(bed_type.id):
        db.session.rollback()
        raise HoldError(f"Sorry, there are no open beds left in “{bed_type.label}”.")

    hold = Hold(user_id=user.id, bed_type_id=bed_type.id)  # expires_at defaults to 60 minutes
    db.session.add(hold)
    db.session.commit()
    return hold


def cancel_hold(hold):
    """Cancel an active hold and release its bed."""
    if not _change_status(hold.id, HoldStatus.CANCELLED):
        db.session.rollback()
        raise HoldError("Only active holds can be cancelled.")
    _release_bed(hold.bed_type_id)
    db.session.commit()


def confirm_hold(hold):
    """Mark an active hold as checked in. The bed stays occupied, so available doesn't change."""
    if not _change_status(hold.id, HoldStatus.CONFIRMED):
        db.session.rollback()
        raise HoldError("Only active holds can be checked in.")
    db.session.commit()
