from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from crypto_trader.adapters.coinbase import CoinbaseFeed
from crypto_trader.alerts import Alerter
from crypto_trader.config import load_config, save_config
from crypto_trader.db import Database
from crypto_trader.health import Heartbeat
from crypto_trader.loop import Engine
from crypto_trader.models import Position, PositionStatus, Quote
from crypto_trader.paper import PaperBroker
from crypto_trader.risk import RiskEngine


class FakeFeed(CoinbaseFeed):
    def __init__(self, quote: Quote):
        self.quote = quote
        self.last_date_header = "Mon, 09 Mar 2026 15:00:00 GMT"

    def get_ticker(self, symbol: str) -> Quote:
        return self.quote

    def get_candles(self, symbol: str, granularity: int, limit: int = 300):
        return []

    def startup_clock_warning(self):
        return None


def _engine(env_settings, quote: Quote) -> Engine:
    cfg = load_config(env_settings.config_path, env_settings)
    db = Database(env_settings.db_path)
    health = Heartbeat(timedelta(seconds=90))
    return Engine(
        env_settings,
        cfg,
        db,
        health,
        Alerter(None),
        FakeFeed(quote),
        PaperBroker(cfg.fee_bps),
        RiskEngine(cfg),
        sleep=lambda _s: None,
        fatal_on_error=False,
    )


def test_stale_quote_blocks_entry(env_settings):
    old = Quote(
        ts=datetime.now(tz=UTC) - timedelta(seconds=120),
        symbol="BTC-USD",
        bid=Decimal("100"),
        ask=Decimal("100.1"),
        source="test",
    )
    engine = _engine(env_settings, old)
    engine.tick()
    assert engine.block_entries is True


def test_config_hot_reload_keeps_stored_exits(env_settings):
    quote = Quote(
        ts=datetime.now(tz=UTC),
        symbol="BTC-USD",
        bid=Decimal("100"),
        ask=Decimal("100.1"),
        source="test",
    )
    engine = _engine(env_settings, quote)
    pos = engine.db.insert_position(
        Position(
            id=None,
            symbol="BTC-USD",
            qty=Decimal("0.01"),
            entry_price=Decimal("100"),
            stop=Decimal("95"),
            target=Decimal("110"),
            opened_at=datetime.now(tz=UTC),
            entry_fee=Decimal("0.1"),
            cost_basis=Decimal("1.1"),
            status=PositionStatus.OPEN,
        )
    )
    engine.config_mtime = 0
    save_config(env_settings.config_path, {"stop_atr_mult": 9.9, "target_atr_mult": 9.9}, env_settings)
    engine.maybe_reload_config()
    loaded = engine.db.open_position()
    assert loaded is not None
    assert loaded.stop == Decimal("95")
    assert loaded.target == Decimal("110")
    assert pos.stop == loaded.stop


def test_tick_records_entry_skip_when_candles_missing(env_settings):
    quote = Quote(
        ts=datetime.now(tz=UTC),
        symbol="BTC-USD",
        bid=Decimal("100"),
        ask=Decimal("100.1"),
        source="test",
    )
    engine = _engine(env_settings, quote)
    engine.cfg.session_start = "00:00"
    engine.cfg.session_end = "23:59"
    engine.tick()
    assert engine.skip_counts.get("no_candles", 0) >= 1
    assert engine.last_skips.get("BTC-USD") == "no_candles"
    assert engine.risk_adjust is not None
