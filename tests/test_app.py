from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from crypto_trader.app import Runtime, create_app
from crypto_trader.models import Position, PositionStatus, Quote, Trade


def _logged_in(env_settings):
    rt = Runtime(env_settings, start_loop=False)
    rt.health.touch(reason="ok")
    app = create_app(rt, start_loop=False)
    client = TestClient(app)
    client.post("/login", data={"password": "secret"})
    return client, rt


def test_dead_trading_thread_makes_healthcheck_fail(env_settings):
    rt = Runtime(env_settings, start_loop=False)
    app = create_app(rt, start_loop=False)
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 503
    assert resp.json()["ok"] is False


def test_paused_loop_with_fresh_heartbeat_is_healthy(env_settings):
    rt = Runtime(env_settings, start_loop=False)
    rt.health.touch(paused=True, reason="session")
    app = create_app(rt, start_loop=False)
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["paused"] is True


def test_login_rate_limit_and_session(env_settings):
    rt = Runtime(env_settings, start_loop=False)
    rt.health.touch(reason="ok")
    app = create_app(rt, start_loop=False)
    client = TestClient(app)
    bad = client.post("/login", data={"password": "nope"})
    assert bad.status_code == 401
    ok = client.post("/login", data={"password": "secret"}, follow_redirects=False)
    assert ok.status_code == 303
    assert "session" in ok.headers.get("set-cookie", "").lower()


def test_dashboard_and_admin_and_trades(env_settings):
    client, rt = _logged_in(env_settings)
    rt.db.insert_trade(
        Trade(
            id=None,
            opened_at=datetime(2026, 3, 9, 15, 0, tzinfo=UTC),
            closed_at=datetime(2026, 3, 9, 15, 10, tzinfo=UTC),
            symbol="BTC-USD",
            side="long",
            qty=Decimal("0.01"),
            entry_price=Decimal("100"),
            exit_price=Decimal("101"),
            entry_fee=Decimal("0.10"),
            exit_fee=Decimal("0.10"),
            pnl=Decimal("0.80"),
            cost_basis=Decimal("1.10"),
            reason="target",
            mode="paper",
        )
    )
    dash = client.get("/")
    assert dash.status_code == 200
    assert b"Latest trades" in dash.content
    assert b"0.80" in dash.content
    trades = client.get("/trades")
    assert trades.status_code == 200
    assert b"Trade blotter" in trades.content
    assert b"cost basis" in trades.content.lower() or b"Cost basis" in trades.content
    admin = client.get("/settings")
    assert admin.status_code == 200
    assert b"Admin" in admin.content
    assert b"Stop ATR multiple" in admin.content
    assert b"Reset all risk counters" in admin.content


def test_admin_saves_stop_and_resets_risk(env_settings):
    client, rt = _logged_in(env_settings)
    rt.risk.record_realized(Decimal("-12"))
    saved = client.post(
        "/settings",
        data={"stop_atr_mult": "1.8", "ema_fast": "9", "ema_slow": "21"},
        follow_redirects=False,
    )
    assert saved.status_code == 303
    assert rt.cfg.stop_atr_mult == 1.8
    reset = client.post("/reset-daily", follow_redirects=False)
    assert reset.status_code == 303
    assert rt.risk.state.daily_pnl == Decimal("0")


def test_flatten_open_position(env_settings):
    client, rt = _logged_in(env_settings)
    rt.engine.last_quote = Quote(
        ts=datetime.now(tz=UTC),
        symbol="BTC-USD",
        bid=Decimal("99"),
        ask=Decimal("100"),
        source="test",
    )
    rt.db.insert_position(
        Position(
            id=None,
            symbol="BTC-USD",
            qty=Decimal("0.1"),
            entry_price=Decimal("100"),
            stop=Decimal("95"),
            target=Decimal("110"),
            opened_at=datetime.now(tz=UTC),
            entry_fee=Decimal("1.0"),
            cost_basis=Decimal("11"),
            status=PositionStatus.OPEN,
        )
    )
    resp = client.post("/flatten", follow_redirects=False)
    assert resp.status_code == 303
    assert rt.db.open_position() is None
    assert rt.db.all_trades()
