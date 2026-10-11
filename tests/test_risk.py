from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from crypto_trader.config import BotConfig
from crypto_trader.models import HaltReason, Position, PositionStatus, Quote
from crypto_trader.risk import RiskEngine


def test_daily_loss_includes_unrealized_and_resets_next_day():
    cfg = BotConfig(daily_loss_limit_usd=Decimal("50"), weekly_loss_limit_usd=Decimal("500"), cumulative_loss_limit_usd=Decimal("500"))
    engine = RiskEngine(cfg)
    monday = datetime(2026, 3, 9, 15, 0, tzinfo=ZoneInfo("America/Chicago")).astimezone(UTC)
    engine.record_realized(Decimal("-20"))
    halt = engine.check(monday)
    assert halt is HaltReason.NONE
    engine.record_realized(Decimal("-40"))
    halt = engine.check(monday)
    assert halt is HaltReason.DAILY_LOSS
    tuesday = datetime(2026, 3, 10, 9, 0, tzinfo=ZoneInfo("America/Chicago")).astimezone(UTC)
    halt = engine.check(tuesday)
    assert halt is HaltReason.NONE
    assert engine.state.daily_pnl == Decimal("0")


def test_weekly_loss_requires_manual_resume():
    cfg = BotConfig(daily_loss_limit_usd=Decimal("500"), weekly_loss_limit_usd=Decimal("50"), cumulative_loss_limit_usd=Decimal("500"))
    engine = RiskEngine(cfg)
    ts = datetime(2026, 3, 9, 15, 0, tzinfo=ZoneInfo("America/Chicago")).astimezone(UTC)
    engine.record_realized(Decimal("-60"))
    halt = engine.check(ts)
    assert halt is HaltReason.WEEKLY_LOSS
    assert engine.state.manual_resume_required is True
    later = datetime(2026, 3, 11, 15, 0, tzinfo=ZoneInfo("America/Chicago")).astimezone(UTC)
    halt = engine.check(later)
    assert halt is HaltReason.WEEKLY_LOSS
    engine.manual_resume()
    assert engine.check(later) is HaltReason.NONE


def test_operator_reset_clears_counters():
    cfg = BotConfig(
        daily_loss_limit_usd=Decimal("50"),
        weekly_loss_limit_usd=Decimal("50"),
        cumulative_loss_limit_usd=Decimal("50"),
    )
    engine = RiskEngine(cfg)
    engine.record_realized(Decimal("-40"))
    engine.reset_daily()
    assert engine.state.daily_pnl == Decimal("0")
    engine.record_realized(Decimal("-40"))
    engine.reset_risk_counters()
    assert engine.state.weekly_pnl == Decimal("0")
    assert engine.state.manual_resume_required is False


def test_daily_loss_sums_unrealized_across_coins():
    cfg = BotConfig(
        daily_loss_limit_usd=Decimal("20"),
        weekly_loss_limit_usd=Decimal("500"),
        cumulative_loss_limit_usd=Decimal("500"),
    )
    engine = RiskEngine(cfg)
    ts = datetime(2026, 3, 9, 15, 0, tzinfo=ZoneInfo("America/Chicago")).astimezone(UTC)
    positions = [
        Position(
            id=1,
            symbol="BTC-USD",
            qty=Decimal("1"),
            entry_price=Decimal("100"),
            stop=Decimal("90"),
            target=Decimal("120"),
            opened_at=ts,
            entry_fee=Decimal("0"),
            cost_basis=Decimal("100"),
            status=PositionStatus.OPEN,
        ),
        Position(
            id=2,
            symbol="ETH-USD",
            qty=Decimal("1"),
            entry_price=Decimal("50"),
            stop=Decimal("40"),
            target=Decimal("80"),
            opened_at=ts,
            entry_fee=Decimal("0"),
            cost_basis=Decimal("50"),
            status=PositionStatus.OPEN,
        ),
    ]
    quotes = {
        "BTC-USD": Quote(ts=ts, symbol="BTC-USD", bid=Decimal("90"), ask=Decimal("91"), source="t"),
        "ETH-USD": Quote(ts=ts, symbol="ETH-USD", bid=Decimal("40"), ask=Decimal("41"), source="t"),
    }
    assert engine.check(ts, positions, quotes) is HaltReason.DAILY_LOSS
