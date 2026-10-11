from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from crypto_trader.timeutil import is_session_open


def test_chicago_halt_across_dst_spring_forward():
    # 2026-03-08 is the US spring-forward Sunday. 02:00 CST does not exist.
    pre = datetime(2026, 3, 8, 1, 30, tzinfo=ZoneInfo("America/Chicago"))
    after = datetime(2026, 3, 8, 8, 0, tzinfo=ZoneInfo("America/Chicago"))
    assert is_session_open(pre, "America/Chicago", "08:00", "20:00") is False
    assert is_session_open(after, "America/Chicago", "08:00", "20:00") is True
    # 08:00 CDT is still 08:00 local after the jump.
    assert after.dst().total_seconds() != 0


def test_chicago_halt_across_dst_fall_back():
    # 2026-11-01 is the US fall-back Sunday. 01:00 happens twice.
    first = datetime(2026, 11, 1, 1, 30, tzinfo=ZoneInfo("America/Chicago"))
    session = datetime(2026, 11, 1, 9, 0, tzinfo=ZoneInfo("America/Chicago"))
    assert is_session_open(first, "America/Chicago", "08:00", "20:00") is False
    assert is_session_open(session, "America/Chicago", "08:00", "20:00") is True
