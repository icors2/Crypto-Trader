from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

from crypto_trader.timeutil import now_utc


def parse_http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        ts = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts


def clock_skew_seconds(http_date: str | None, local: datetime | None = None) -> float | None:
    remote = parse_http_date(http_date)
    if remote is None:
        return None
    here = local or now_utc()
    return abs((here - remote).total_seconds())


def skew_warning(http_date: str | None, threshold: float = 5.0) -> str | None:
    skew = clock_skew_seconds(http_date)
    if skew is None:
        return None
    if skew > threshold:
        return f"clock skew {skew:.1f}s exceeds {threshold:.0f}s"
    return None
