from __future__ import annotations

import json
import logging
import os
import threading
from contextlib import asynccontextmanager
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from crypto_trader.adapters.coinbase import CoinbaseFeed
from crypto_trader.alerts import Alerter
from crypto_trader.auth import Auth
from crypto_trader.config import ConfigError, load_config, save_config
from crypto_trader.db import Database
from crypto_trader.health import Heartbeat
from crypto_trader.loop import Engine
from crypto_trader.models import ExitReason
from crypto_trader.paper import PaperBroker
from crypto_trader.reports import trade_report, trades_to_csv
from crypto_trader.risk import RiskEngine
from crypto_trader.settings import EnvSettings
from crypto_trader.timeutil import now_utc

log = logging.getLogger(__name__)
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


class Runtime:
    def __init__(self, settings: EnvSettings | None = None, start_loop: bool = True) -> None:
        self.settings = settings or EnvSettings()
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.settings.config_path.exists():
            from shutil import copyfile

            bundled = Path("config/config.yaml")
            if bundled.exists():
                copyfile(bundled, self.settings.config_path)
        self.cfg = load_config(self.settings.config_path, self.settings)
        self.db = Database(self.settings.db_path)
        stale = timedelta(seconds=max(90, self.cfg.poll_interval_sec * 4))
        self.health = Heartbeat(stale)
        self.alerts = Alerter(self.settings.ntfy_topic, self.settings.ntfy_url)
        self.auth = Auth(self.settings)
        self.feed = CoinbaseFeed()
        self.broker = PaperBroker(self.cfg.fee_bps, self.cfg.slippage_bps)
        self.broker.cash = self.cfg.paper_starting_cash
        if self.cfg.mode == "live":
            if not (
                self.settings.robinhood_api_key
                and self.settings.robinhood_private_key
                and self.settings.robinhood_account_number
            ):
                raise RuntimeError("live mode requires ROBINHOOD_API_KEY, ROBINHOOD_PRIVATE_KEY, ROBINHOOD_ACCOUNT_NUMBER")
            from crypto_trader.adapters.robinhood import RobinhoodClient
            from crypto_trader.live import LiveBroker

            self.broker = LiveBroker(
                RobinhoodClient(
                    self.settings.robinhood_api_key,
                    self.settings.robinhood_private_key,
                    self.settings.robinhood_account_number,
                )
            )
        self.risk = RiskEngine(self.cfg)
        self.engine = Engine(
            self.settings,
            self.cfg,
            self.db,
            self.health,
            self.alerts,
            self.feed,
            self.broker,
            self.risk,
        )
        self.start_loop = start_loop
        self.thread: threading.Thread | None = None

    def boot_loop(self) -> None:
        if not self.start_loop:
            return
        self.thread = threading.Thread(target=self.engine.run_forever, name="trading-loop", daemon=True)
        self.thread.start()


def create_app(runtime: Runtime | None = None, start_loop: bool = True) -> FastAPI:
    rt = runtime or Runtime(start_loop=start_loop)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
        if rt.auth.generated_password:
            log.warning("Generated UI password (set UI_PASSWORD_HASH): %s", rt.auth.generated_password)
        rt.boot_loop()
        yield
        rt.engine.stop_event.set()

    app = FastAPI(title="Crypto day trader", lifespan=lifespan)
    secret = rt.settings.ui_session_secret
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret,
        same_site="strict",
        https_only=rt.settings.secure_cookies,
        max_age=12 * 60 * 60,
    )
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.state.rt = rt

    def logged_in(request: Request) -> bool:
        return rt.auth.load_session(request.cookies.get("session")) is not None

    def require_login(request: Request) -> RedirectResponse | None:
        if not logged_in(request):
            return RedirectResponse("/login", status_code=303)
        return None

    @app.get("/healthz")
    def healthz() -> Response:
        snap = rt.health.snapshot()
        payload = {
            "ok": snap.ok,
            "status": snap.status,
            "paused": snap.paused,
            "fatal": snap.fatal,
            "heartbeat_age_sec": snap.heartbeat_age_sec,
        }
        return Response(
            content=json.dumps(payload),
            media_type="application/json",
            status_code=200 if snap.ok else 503,
        )

    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "login.html", {"error": None})

    @app.post("/login")
    def login(request: Request, password: str = Form(...)) -> Response:
        ip = request.client.host if request.client else "unknown"
        if rt.auth.rate_limited(ip):
            return templates.TemplateResponse(
                request, "login.html", {"error": "Too many attempts. Try later."}, status_code=429
            )
        rt.auth.record_attempt(ip)
        if not rt.auth.verify_password(password):
            return templates.TemplateResponse(request, "login.html", {"error": "Invalid password."}, status_code=401)
        token = rt.auth.issue_session()
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(
            "session",
            token,
            httponly=True,
            samesite="strict",
            secure=rt.settings.secure_cookies,
            max_age=12 * 60 * 60,
        )
        return resp

    @app.post("/logout")
    def logout() -> Response:
        resp = RedirectResponse("/login", status_code=303)
        resp.delete_cookie("session")
        return resp

    def _notice(request: Request) -> str | None:
        return request.query_params.get("notice")

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        snap = rt.health.snapshot()
        pos = rt.db.open_position()
        trades = rt.db.list_trades(10)
        report = trade_report(rt.db.all_trades())
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "cfg": rt.cfg,
                "health": snap,
                "position": pos,
                "trades": trades,
                "report": report,
                "risk": rt.risk.state,
                "quote": rt.engine.last_quote,
                "block_entries": rt.engine.block_entries,
                "notice": _notice(request),
                "events": rt.db.recent_events(8),
            },
        )

    @app.get("/trades", response_class=HTMLResponse)
    def trades_page(request: Request) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        trades = rt.db.list_trades(500)
        report = trade_report(rt.db.all_trades())
        return templates.TemplateResponse(
            request,
            "trades.html",
            {"trades": trades, "report": report, "notice": _notice(request)},
        )

    @app.get("/settings", response_class=HTMLResponse)
    def settings_form(request: Request, error: str | None = None) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "cfg": rt.cfg,
                "env": rt.settings,
                "error": error,
                "notice": _notice(request),
                "risk": rt.risk.state,
                "position": rt.db.open_position(),
                "audits": rt.db.list_config_audit(15),
            },
        )

    @app.post("/settings")
    async def save_settings(request: Request) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        form = await request.form()
        updates: dict[str, Any] = {}
        bool_fields = {"htf_filter_enabled", "flatten_on_session_end"}
        int_fields = {
            "timeframe_seconds",
            "ema_fast",
            "ema_slow",
            "atr_period",
            "poll_interval_sec",
            "fee_bps",
            "spread_max_bps",
            "cooldown_bars",
            "max_hold_minutes",
            "htf_ema_period",
            "htf_timeframe_seconds",
            "slippage_bps",
            "stale_quote_sec",
            "max_failed_polls",
        }
        dec_fields = {
            "max_notional_usd",
            "daily_loss_limit_usd",
            "weekly_loss_limit_usd",
            "cumulative_loss_limit_usd",
            "cost_multiple",
            "min_order_size",
            "dust_notional_usd",
            "paper_starting_cash",
        }
        float_fields = {"stop_atr_mult", "target_atr_mult"}
        for key in (
            "mode",
            "symbol",
            "timezone",
            "session_start",
            "session_end",
            *int_fields,
            *dec_fields,
            *float_fields,
            *bool_fields,
        ):
            if key not in form:
                continue
            raw = str(form[key])
            if key in bool_fields:
                updates[key] = raw in {"1", "true", "on", "yes"}
            elif key in int_fields:
                updates[key] = int(raw)
            elif key in float_fields:
                updates[key] = float(raw)
            elif key in dec_fields:
                updates[key] = Decimal(raw)
            else:
                updates[key] = raw
        old = json.dumps(rt.cfg.as_public_dict())
        try:
            rt.cfg = save_config(rt.settings.config_path, updates, rt.settings)
        except ConfigError as exc:
            return settings_form(request, error=str(exc))
        rt.engine.cfg = rt.cfg
        rt.risk.cfg = rt.cfg
        rt.broker.fee_bps = rt.cfg.fee_bps
        rt.broker.slippage_bps = rt.cfg.slippage_bps
        rt.db.record_config_audit(now_utc(), "ui", old, json.dumps(rt.cfg.as_public_dict()))
        return RedirectResponse("/settings?notice=saved", status_code=303)

    @app.post("/halt")
    def halt(request: Request) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        rt.settings.stop_path.write_text("halt\n", encoding="utf-8")
        rt.alerts.send("manual halt", "STOP file written")
        return RedirectResponse("/?notice=halted", status_code=303)

    @app.post("/resume")
    def resume(request: Request) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        if rt.settings.stop_path.exists():
            rt.settings.stop_path.unlink()
        rt.risk.manual_resume()
        rt.alerts.send("manual resume", "operator resumed trading")
        return RedirectResponse("/?notice=resumed", status_code=303)

    @app.post("/flatten")
    def flatten(request: Request) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        pos = rt.db.open_position()
        quote = rt.engine.last_quote
        if pos is None:
            return RedirectResponse("/?notice=flat", status_code=303)
        if quote is None:
            return RedirectResponse("/settings?notice=no_quote", status_code=303)
        rt.engine._close(pos, quote, ExitReason.MANUAL)
        rt.alerts.send("manual flatten", f"closed {pos.symbol}")
        return RedirectResponse("/trades?notice=flattened", status_code=303)

    @app.post("/reset-daily")
    def reset_daily(request: Request) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        rt.risk.reset_daily()
        rt.db.record_event("info", "reset_daily", "operator reset daily PnL", now_utc())
        return RedirectResponse("/settings?notice=daily_reset", status_code=303)

    @app.post("/reset-risk")
    def reset_risk(request: Request) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        if rt.settings.stop_path.exists():
            rt.settings.stop_path.unlink()
        rt.risk.reset_risk_counters()
        rt.engine.cooldown_remaining = 0
        rt.engine.block_entries = False
        rt.db.record_event("info", "reset_risk", "operator reset risk counters", now_utc())
        return RedirectResponse("/settings?notice=risk_reset", status_code=303)

    @app.get("/trades.csv")
    def export_csv(request: Request) -> Response:
        denied = require_login(request)
        if denied:
            return denied
        body = trades_to_csv(rt.db.all_trades())
        return Response(
            content=body,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=trades.csv"},
        )

    return app


def get_app() -> FastAPI:
    start = os.environ.get("START_LOOP", "1") != "0"
    return create_app(start_loop=start)


app = get_app()
