"""Jinja template filters.

Times are stored in UTC. Use the `pacific` filter to show them in shelter-local time:

    {{ bed_type.updated_at|pacific }}               -> "Nov 09, 05:04 PM PST"
    {{ review.created_at|pacific('%b %d, %Y') }}    -> "Nov 09, 2026"
"""
from datetime import timezone
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")
DEFAULT_FORMAT = "%b %d, %I:%M %p %Z"


def to_pacific(dt):
    """Convert a stored UTC datetime to Pacific time (handles PST/PDT)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # SQLite drops the timezone on read; everything we store is UTC.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PACIFIC)


def pacific(dt, fmt=DEFAULT_FORMAT):
    local = to_pacific(dt)
    return local.strftime(fmt) if local else ""


def register_filters(app):
    app.jinja_env.filters["pacific"] = pacific
