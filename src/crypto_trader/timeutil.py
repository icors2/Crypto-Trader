from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo


def zone(name: str) -> ZoneInfo:
    return ZoneInfo(name)


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def to_local(ts: datetime, tz_name: str) -> datetime:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.astimezone(zone(tz_name))


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def is_session_open(ts: datetime, tz_name: str, start: str, end: str) -> bool:
    """True when local time is inside [start, end). Handles overnight windows and DST."""
    local = to_local(ts, tz_name)
    t = local.timetz().replace(tzinfo=None)
    start_t = parse_hhmm(start)
    end_t = parse_hhmm(end)
    if start_t == end_t:
        return True
    if start_t < end_t:
        return start_t <= t < end_t
    return t >= start_t or t < end_t


def chicago_day_key(ts: datetime, tz_name: str = "America/Chicago") -> str:
    return to_local(ts, tz_name).date().isoformat()


def chicago_week_key(ts: datetime, tz_name: str = "America/Chicago") -> str:
    local = to_local(ts, tz_name).date()
    iso = local.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"
