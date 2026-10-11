from __future__ import annotations

from datetime import UTC, datetime

from crypto_trader.clock import clock_skew_seconds


def test_clock_skew_warning():
    local = datetime(2026, 3, 9, 15, 0, 30, tzinfo=UTC)
    header = "Mon, 09 Mar 2026 15:00:00 GMT"
    skew = clock_skew_seconds(header, local)
    assert skew == 30
    assert skew > 5


def test_clock_skew_from_fixed_local():
    header = "Mon, 09 Mar 2026 15:00:00 GMT"
    local = datetime(2026, 3, 9, 15, 0, 30, tzinfo=UTC)
    assert clock_skew_seconds(header, local) > 5
