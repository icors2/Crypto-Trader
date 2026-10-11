from __future__ import annotations

from datetime import timedelta

from crypto_trader.health import Heartbeat


def test_dead_loop_fails_healthcheck():
    hb = Heartbeat(stale_after=timedelta(seconds=1))
    snap = hb.snapshot()
    assert snap.ok is False
    assert snap.status == "no_heartbeat"


def test_stale_heartbeat_fails():
    hb = Heartbeat(stale_after=timedelta(seconds=0))
    hb.touch(reason="ok")
    snap = hb.snapshot()
    assert snap.ok is False
    assert snap.status == "stale_heartbeat"


def test_paused_is_still_healthy():
    hb = Heartbeat(stale_after=timedelta(seconds=60))
    hb.touch(paused=True, reason="session")
    snap = hb.snapshot()
    assert snap.ok is True
    assert snap.paused is True
