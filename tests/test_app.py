from __future__ import annotations

from fastapi.testclient import TestClient

from crypto_trader.app import Runtime, create_app


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
