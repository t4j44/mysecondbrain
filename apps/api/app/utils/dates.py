import zoneinfo
from datetime import datetime, timedelta, timezone
from typing import Optional


def now_utc() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def validate_date_range(start_time: Optional[datetime], end_time: Optional[datetime]) -> bool:
    """Ensure end_time does not precede start_time."""
    if start_time and end_time:
        return end_time >= start_time
    return True


def get_user_today_bounds(tz_name: str = "UTC") -> tuple[datetime, datetime]:
    """Calculate the absolute UTC bounds for 'today' in the user's local timezone."""
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = zoneinfo.ZoneInfo("UTC")

    now_local = datetime.now(tz)
    start_of_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)

    # Convert back to UTC for database querying against TIMESTAMPTZ columns
    return start_of_day.astimezone(timezone.utc), end_of_day.astimezone(timezone.utc)
