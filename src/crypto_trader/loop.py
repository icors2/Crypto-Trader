from __future__ import annotations

import json
import logging
import threading
from datetime import timedelta
from decimal import Decimal

from crypto_trader.adapters.coinbase import CoinbaseError, CoinbaseFeed
from crypto_trader.alerts import Alerter
from crypto_trader.config import BotConfig, load_config
from crypto_trader.db import Database
from crypto_trader.fills import quote_exit
from crypto_trader.health import Heartbeat
from crypto_trader.indicators import compute_indicators
from crypto_trader.models import (
    ExitReason,
    HaltReason,
    OrderStatus,
    Position,
    PositionStatus,
    Quote,
    Side,
    Trade,
)
from crypto_trader.money import D, money
from crypto_trader.paper import PaperBroker
from crypto_trader.reconcile import is_dust, paper_lookup, reconcile_pending
from crypto_trader.risk import RiskEngine
from crypto_trader.settings import EnvSettings
from crypto_trader.strategy import evaluate_entry, position_exits
from crypto_trader.timeutil import is_session_open, now_utc

log = logging.getLogger(__name__)


class Engine:
    def __init__(
        self,
        settings: EnvSettings,
        cfg: BotConfig,
        db: Database,
        health: Heartbeat,
        alerts: Alerter,
        feed: CoinbaseFeed,
        broker: PaperBroker,
        risk: RiskEngine,
        sleep=None,
        fatal_on_error: bool = True,
    ) -> None:
        self.settings = settings
        self.cfg = cfg
        self.db = db
        self.health = health
        self.alerts = alerts
        self.feed = feed
        self.broker = broker
        self.risk = risk
        self._sleep = sleep or _sleep
        self.fatal_on_error = fatal_on_error
        self.stop_event = threading.Event()
        self.failed_polls = 0
        self.last_quote: Quote | None = None
        self.cooldown_remaining = 0
        self.last_bar_ts = None
        self.block_entries = False
        self.config_mtime: float | None = None

    def run_forever(self) -> None:
        self.alerts.send("trader restart", "trading loop starting")
        try:
            self.startup()
            while not self.stop_event.is_set():
                self.tick()
                self._sleep(self.cfg.poll_interval_sec)
        except Exception as exc:  # noqa: BLE001
            log.exception("fatal trading loop error")
            self.health.mark_fatal(str(exc))
            self.alerts.send("trader fatal", str(exc), priority="high")
            if self.fatal_on_error:
                raise SystemExit(1) from exc

    def startup(self) -> None:
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        warn = self.feed.startup_clock_warning()
        if warn:
            self.db.record_event("warning", "clock_skew", warn, now_utc())
            self.alerts.send("clock skew", warn, priority="high")
        result = reconcile_pending(
            self.db,
            paper_lookup(self.broker),
            min_order_size=self.cfg.min_order_size,
            dust_notional=self.cfg.dust_notional_usd,
            mark_price=self.last_quote.mid if self.last_quote else None,
        )
        for item in result.dust:
            self.db.record_event("warning", "dust", item, now_utc())
            self.alerts.send("dust position", item)
        for item in result.mismatches:
            self.db.record_event("warning", "reconcile", item, now_utc())
            self.alerts.send("reconcile mismatch", item, priority="high")
        self.health.touch(reason="started")

    def maybe_reload_config(self) -> None:
        path = self.settings.config_path
        if not path.exists():
            return
        mtime = path.stat().st_mtime
        if self.config_mtime is None:
            self.config_mtime = mtime
            return
        if mtime == self.config_mtime:
            return
        self.config_mtime = mtime
        old = self.cfg.as_public_dict()
        self.cfg = load_config(path, self.settings)
        self.risk.cfg = self.cfg
        self.broker.fee_bps = self.cfg.fee_bps
        self.broker.slippage_bps = self.cfg.slippage_bps
        self.db.record_config_audit(now_utc(), "hot-reload", json.dumps(old), json.dumps(self.cfg.as_public_dict()))

    def tick(self) -> None:
        self.maybe_reload_config()
        stop_file = self.settings.stop_path.exists()
        now = now_utc()
        session = is_session_open(now, self.cfg.timezone, self.cfg.session_start, self.cfg.session_end)
        position = self.db.open_position()
        quote = self._poll_quote()
        halt = self.risk.check(now, position, quote, stop_file=stop_file, session_open=session)
        paused = halt is not HaltReason.NONE
        self.health.touch(paused=paused, reason=halt.value if paused else "ok")
        if quote is None:
            return
        if position and halt in {HaltReason.STOP_FILE, HaltReason.DAILY_LOSS, HaltReason.WEEKLY_LOSS, HaltReason.CUMULATIVE_LOSS}:
            # still manage exits while halted except we keep protecting the position
            self._manage_position(position, quote, now)
            return
        if position:
            self._manage_position(position, quote, now)
            return
        if paused or self.block_entries:
            return
        self._maybe_enter(quote, now)

    def _poll_quote(self) -> Quote | None:
        try:
            ticker = self.feed.get_ticker(self.cfg.symbol)
            quote = self.broker.get_quote(self.cfg.symbol, ticker)
            self.db.record_quote(quote)
            self.last_quote = quote
            self.failed_polls = 0
            self.block_entries = False
            age = (now_utc() - quote.ts).total_seconds()
            if age > self.cfg.stale_quote_sec:
                self.block_entries = True
                self.db.record_event("warning", "stale_quote", f"age={age:.1f}s", now_utc())
                self.alerts.send("stale quote", f"{self.cfg.symbol} age {age:.1f}s")
            return quote
        except (CoinbaseError, Exception) as exc:  # noqa: BLE001
            self.failed_polls += 1
            log.warning("quote poll failed: %s", exc)
            if self.failed_polls >= self.cfg.max_failed_polls:
                self.block_entries = True
                self.db.record_event("warning", "stale_quote", f"failed_polls={self.failed_polls}", now_utc())
                self.alerts.send("quote failures", str(exc))
            if self.last_quote and (now_utc() - self.last_quote.ts).total_seconds() > self.cfg.stale_quote_sec:
                self.block_entries = True
            return self.last_quote

    def _manage_position(self, position: Position, quote: Quote, now) -> None:
        fill = quote_exit(quote, position, self.cfg.slippage_bps)
        held = (now - position.opened_at) >= timedelta(minutes=self.cfg.max_hold_minutes)
        flatten = (not is_session_open(now, self.cfg.timezone, self.cfg.session_start, self.cfg.session_end)) and self.cfg.flatten_on_session_end
        if not fill and not held and not flatten:
            return
        reason = fill.reason if fill else (ExitReason.MAX_HOLD if held else ExitReason.FLATTEN)
        self._close(position, quote, reason)

    def _close(self, position: Position, quote: Quote, reason: ExitReason) -> None:
        if is_dust(position.qty, quote.bid, self.cfg.min_order_size, self.cfg.dust_notional_usd):
            position.status = PositionStatus.DUST
            self.db.update_position(position)
            self.db.record_event("warning", "dust", f"position {position.id}", now_utc())
            self.alerts.send("dust", f"cannot sell {position.qty} {position.symbol}")
            return
        order = self.broker.place_order(Side.SELL, position.symbol, position.qty, quote)
        self.db.upsert_order(order)
        if order.status in {OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED} and order.average_price:
            qty = order.filled_qty
            exit_price = order.average_price
            exit_fee = order.fee_charged
            pnl = money((exit_price - position.entry_price) * qty - position.entry_fee - exit_fee)
            trade = Trade(
                id=None,
                opened_at=position.opened_at,
                closed_at=now_utc(),
                symbol=position.symbol,
                side="long",
                qty=qty,
                entry_price=position.entry_price,
                exit_price=exit_price,
                entry_fee=position.entry_fee,
                exit_fee=exit_fee,
                pnl=pnl,
                cost_basis=position.cost_basis,
                reason=reason.value,
                mode=self.cfg.mode,
            )
            self.db.insert_trade(trade)
            self.risk.record_realized(pnl)
            if reason is ExitReason.STOP:
                self.cooldown_remaining = self.cfg.cooldown_bars
            if order.status is OrderStatus.PARTIALLY_FILLED:
                remain = position.qty - qty
                if is_dust(remain, quote.bid, self.cfg.min_order_size, self.cfg.dust_notional_usd):
                    position.qty = remain
                    position.status = PositionStatus.DUST
                    self.db.update_position(position)
                    self.alerts.send("dust leftover", str(remain))
                    return
                position.qty = remain
                self.db.update_position(position)
                return
            position.status = PositionStatus.CLOSED
            position.qty = Decimal("0")
            self.db.update_position(position)

    def _maybe_enter(self, quote: Quote, now) -> None:
        try:
            bars = self.feed.get_candles(self.cfg.symbol, self.cfg.timeframe_seconds)
            htf = None
            if self.cfg.htf_filter_enabled:
                htf = self.feed.get_candles(self.cfg.symbol, self.cfg.htf_timeframe_seconds)
        except Exception as exc:  # noqa: BLE001
            log.warning("candles failed: %s", exc)
            return
        if not bars:
            return
        if self.last_bar_ts and bars[-1].ts != self.last_bar_ts and self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
        self.last_bar_ts = bars[-1].ts
        closed = bars[:-1] if len(bars) > 1 else bars
        ind = compute_indicators(
            closed,
            ema_fast=self.cfg.ema_fast,
            ema_slow=self.cfg.ema_slow,
            atr_period=self.cfg.atr_period,
            htf_bars=htf[:-1] if htf and len(htf) > 1 else htf,
            htf_ema_period=self.cfg.htf_ema_period,
        )
        if ind is None:
            return
        signal = evaluate_entry(self.cfg, ind, quote, cooldown_remaining=self.cooldown_remaining)
        if not signal.enter_long:
            if signal.skip_reason and signal.skip_reason.startswith("spread"):
                self.db.record_event("info", "spread_skip", signal.skip_reason, now)
            return
        qty = (D(self.cfg.max_notional_usd) / quote.ask).quantize(Decimal("0.00000001"))
        if qty < self.cfg.min_order_size:
            return
        client_id = None
        order = self.broker.place_order(Side.BUY, self.cfg.symbol, qty, quote)
        client_id = order.client_order_id
        self.db.upsert_order(order)
        if order.status is OrderStatus.PENDING:
            return
        if order.filled_qty <= 0 or order.average_price is None:
            return
        entry = order.average_price
        stop, target = position_exits(entry, ind.atr, self.cfg)
        status = PositionStatus.OPEN
        if is_dust(order.filled_qty, entry, self.cfg.min_order_size, self.cfg.dust_notional_usd):
            status = PositionStatus.DUST
            self.alerts.send("dust fill", str(order.filled_qty))
        self.db.insert_position(
            Position(
                id=None,
                symbol=self.cfg.symbol,
                qty=order.filled_qty,
                entry_price=entry,
                stop=stop,
                target=target,
                opened_at=now,
                entry_fee=order.fee_charged,
                cost_basis=money(entry * order.filled_qty + order.fee_charged),
                status=status,
                client_order_id=client_id,
            )
        )


def _sleep(seconds: float) -> None:
    threading.Event().wait(seconds)
