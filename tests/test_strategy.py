from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from crypto_trader.config import BotConfig
from crypto_trader.models import Indicators, Quote
from crypto_trader.strategy import evaluate_entry


def _ind() -> Indicators:
    return Indicators(
        ema_fast=Decimal("101"),
        ema_slow=Decimal("100"),
        atr=Decimal("2"),
        prev_ema_fast=Decimal("99"),
        prev_ema_slow=Decimal("100"),
    )


def test_spread_filter_skips_wide_quote():
    cfg = BotConfig(spread_max_bps=10, fee_bps=0, cost_multiple=Decimal("0.1"))
    quote = Quote(
        ts=datetime(2026, 3, 9, tzinfo=UTC),
        symbol="BTC-USD",
        bid=Decimal("100"),
        ask=Decimal("101"),
        source="test",
    )
    signal = evaluate_entry(cfg, _ind(), quote)
    assert signal.enter_long is False
    assert signal.skip_reason and signal.skip_reason.startswith("spread")


def test_cost_filter_skips_when_target_too_small():
    cfg = BotConfig(spread_max_bps=200, fee_bps=100, cost_multiple=Decimal("50"), target_atr_mult=0.1)
    quote = Quote(
        ts=datetime(2026, 3, 9, tzinfo=UTC),
        symbol="BTC-USD",
        bid=Decimal("100"),
        ask=Decimal("100.05"),
        source="test",
    )
    signal = evaluate_entry(cfg, _ind(), quote)
    assert signal.enter_long is False
    assert signal.skip_reason == "cost_unaware"
