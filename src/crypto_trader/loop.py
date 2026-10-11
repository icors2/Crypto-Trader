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
from crypto_trader.risk_adjust import RiskAdjustSnapshot, apply_risk_level, skip_prefix
from crypto_trader.settings import EnvSettings
from crypto_trader.strategy import evaluate_entry, position_exits
from crypto_trader.timeutil import is_session_open, now_utc

_LOG_SKIP_PREFIXES = frozenset(
    {"cost_unaware", "spread", "cooldown", "htf_unavailable", "htf_downtrend", "no_candles"}
)

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
        self.failed_polls: dict[str, int] = {}
        self.last_quote: Quote | None = None
        self.last_quotes: dict[str, Quote] = {}
        self.cooldown_remaining: dict[str, int] = {}
        self.last_bar_ts: dict[str, object] = {}
        self.block_entries = False
        self.block_entry_symbols: set[str] = set()
        self.config_mtime: float | None = None
        self.effective_cfg = cfg
        self.risk_adjust: RiskAdjustSnapshot | None = None
        self.last_skips: dict[str, str] = {}
        self.skip_counts: dict[str, int] = {}
        self.last_entry_at = None
        self.session_opened_at = None

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
        self._persist_paper()

    def _persist_paper(self) -> None:
        if isinstance(self.broker, PaperBroker):
            self.db.save_paper_account(self.broker.to_account(), now_utc())

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
        watchlist = self.cfg.watchlist()
        positions = self.db.open_positions()
        manage_symbols = {pos.symbol for pos in positions} | set(watchlist)
        quotes: dict[str, Quote] = {}
        for symbol in manage_symbols:
            quote = self._poll_quote(symbol)
            if quote is not None:
                quotes[symbol] = quote
        self.last_quotes = quotes
        if quotes:
            self.last_quote = next(iter(quotes.values()))
        halt = self.risk.check(now, positions, quotes, stop_file=stop_file, session_open=session)
        paused = halt is not HaltReason.NONE
        self._refresh_risk_adjust(now, session)
        self.health.touch(paused=paused, reason=halt.value if paused else "ok")
        if not quotes and not positions:
            if paused:
                self._note_skip("_book", halt.value, now)
            return
        for position in positions:
            quote = quotes.get(position.symbol)
            if quote is None:
                continue
            self._manage_position(position, quote, now)
        if paused or self.block_entries:
            self._note_skip("_book", halt.value if paused else "stale_quote", now)
            return
        open_now = {pos.symbol for pos in self.db.open_positions()}
        slots = self.cfg.max_open_positions - len(open_now)
        if slots <= 0:
            self._note_skip("_book", "max_positions", now)
            return
        for symbol in watchlist:
            if slots <= 0:
                break
            if symbol in open_now or symbol in self.block_entry_symbols:
                continue
            quote = quotes.get(symbol)
            if quote is None:
                continue
            opened = self._maybe_enter_symbol(symbol, quote, now)
            if opened:
                open_now.add(symbol)
                slots -= 1

    def _poll_quote(self, symbol: str | None = None) -> Quote | None:
        pair = symbol or self.cfg.watchlist()[0]
        try:
            ticker = self.feed.get_ticker(pair)
            quote = self.broker.get_quote(pair, ticker)
            self.db.record_quote(quote)
            self.last_quote = quote
            self.last_quotes[pair] = quote
            self.failed_polls[pair] = 0
            self.block_entry_symbols.discard(pair)
            self.block_entries = bool(self.block_entry_symbols)
            age = (now_utc() - quote.ts).total_seconds()
            if age > self.cfg.stale_quote_sec:
                self.block_entry_symbols.add(pair)
                self.block_entries = True
                self.db.record_event("warning", "stale_quote", f"{pair} age={age:.1f}s", now_utc())
                self.alerts.send("stale quote", f"{pair} age {age:.1f}s")
            return quote
        except (CoinbaseError, Exception) as exc:  # noqa: BLE001
            self.failed_polls[pair] = self.failed_polls.get(pair, 0) + 1
            log.warning("quote poll failed for %s: %s", pair, exc)
            if self.failed_polls[pair] >= self.cfg.max_failed_polls:
                self.block_entry_symbols.add(pair)
                self.block_entries = True
                self.db.record_event(
                    "warning", "stale_quote", f"{pair} failed_polls={self.failed_polls[pair]}", now_utc()
                )
                self.alerts.send("quote failures", f"{pair}: {exc}")
            cached = self.last_quotes.get(pair)
            if cached and (now_utc() - cached.ts).total_seconds() > self.cfg.stale_quote_sec:
                self.block_entry_symbols.add(pair)
                self.block_entries = True
            return cached

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
        self._persist_paper()
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
                self.cooldown_remaining[position.symbol] = self.effective_cfg.cooldown_bars
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

    def _maybe_enter(self, quote: Quote, now) -> bool:
        return self._maybe_enter_symbol(quote.symbol, quote, now)

    def _maybe_enter_symbol(self, symbol: str, quote: Quote, now) -> bool:
        try:
            bars = self.feed.get_candles(symbol, self.cfg.timeframe_seconds)
            htf = None
            if self.cfg.htf_filter_enabled:
                htf = self.feed.get_candles(symbol, self.cfg.htf_timeframe_seconds)
        except Exception as exc:  # noqa: BLE001
            log.warning("candles failed for %s: %s", symbol, exc)
            self._note_skip(symbol, "no_candles", now)
            return False
        if not bars:
            self._note_skip(symbol, "no_candles", now)
            return False
        prev_ts = self.last_bar_ts.get(symbol)
        if prev_ts and bars[-1].ts != prev_ts and self.cooldown_remaining.get(symbol, 0) > 0:
            self.cooldown_remaining[symbol] = self.cooldown_remaining.get(symbol, 0) - 1
        self.last_bar_ts[symbol] = bars[-1].ts
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
            self._note_skip(symbol, "no_indicators", now)
            return False
        signal = evaluate_entry(
            self.effective_cfg, ind, quote, cooldown_remaining=self.cooldown_remaining.get(symbol, 0)
        )
        if not signal.enter_long:
            self._note_skip(symbol, signal.skip_reason or "skipped", now)
            return False
        qty = (D(self.effective_cfg.max_notional_usd) / quote.ask).quantize(Decimal("0.00000001"))
        if qty < self.cfg.min_order_size:
            self._note_skip(symbol, "qty_too_small", now)
            return False
        if self.db.open_position(symbol) is not None:
            return False
        order = self.broker.place_order(Side.BUY, symbol, qty, quote)
        client_id = order.client_order_id
        self.db.upsert_order(order)
        self._persist_paper()
        if order.status is OrderStatus.PENDING:
            return False
        if order.filled_qty <= 0 or order.average_price is None:
            return False
        entry = order.average_price
        stop, target = position_exits(entry, ind.atr, self.cfg)
        status = PositionStatus.OPEN
        if is_dust(order.filled_qty, entry, self.cfg.min_order_size, self.cfg.dust_notional_usd):
            status = PositionStatus.DUST
            self.alerts.send("dust fill", f"{symbol} {order.filled_qty}")
        self.db.insert_position(
            Position(
                id=None,
                symbol=symbol,
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
        if status is PositionStatus.OPEN:
            self.last_entry_at = now
        return status is PositionStatus.OPEN

    def _refresh_risk_adjust(self, now, session: bool) -> None:
        if session:
            if self.session_opened_at is None:
                self.session_opened_at = now
        else:
            self.session_opened_at = None
        self.effective_cfg, self.risk_adjust = apply_risk_level(
            self.cfg,
            now=now,
            last_entry_at=self.last_entry_at,
            session_opened_at=self.session_opened_at,
            session_open=session,
            daily_pnl=self.risk.state.daily_pnl,
        )

    def _note_skip(self, symbol: str, reason: str, now) -> None:
        prev = self.last_skips.get(symbol)
        self.last_skips[symbol] = reason
        key = skip_prefix(reason)
        self.skip_counts[key] = self.skip_counts.get(key, 0) + 1
        if prev != reason and key in _LOG_SKIP_PREFIXES:
            self.db.record_event("info", "entry_skip", f"{symbol} {reason}", now)

    def skip_board(self) -> dict[str, object]:
        counts = dict(sorted(self.skip_counts.items(), key=lambda item: (-item[1], item[0])))
        return {
            "counts": counts,
            "last": dict(self.last_skips),
            "total": sum(self.skip_counts.values()),
        }


def _sleep(seconds: float) -> None:
    threading.Event().wait(seconds)
