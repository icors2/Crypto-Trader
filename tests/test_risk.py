from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from crypto_trader.config import BotConfig
from crypto_trader.models import HaltReason
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
