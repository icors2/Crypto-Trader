from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from crypto_trader.timeutil import now_utc


@dataclass
class HealthSnapshot:
    ok: bool
    status: str
    heartbeat_age_sec: float | None
    paused: bool
    fatal: bool


class Heartbeat:
    def __init__(self, stale_after: timedelta) -> None:
        self._lock = threading.Lock()
        self._last: datetime | None = None
        self._paused = False
        self._fatal = False
        self._reason = "starting"
        self.stale_after = stale_after

    def touch(self, *, paused: bool = False, reason: str = "ok") -> None:
        with self._lock:
            self._last = now_utc()
            self._paused = paused
            self._reason = reason

    def mark_fatal(self, reason: str) -> None:
        with self._lock:
            self._fatal = True
            self._reason = reason

    def snapshot(self) -> HealthSnapshot:
        with self._lock:
            last = self._last
            paused = self._paused
            fatal = self._fatal
            reason = self._reason
        if fatal:
            return HealthSnapshot(False, reason, None, paused, True)
        if last is None:
            return HealthSnapshot(False, "no_heartbeat", None, paused, False)
        age = (now_utc() - last).total_seconds()
        stale = age > self.stale_after.total_seconds()
        if stale:
            return HealthSnapshot(False, "stale_heartbeat", age, paused, False)
        return HealthSnapshot(True, reason, age, paused, False)
