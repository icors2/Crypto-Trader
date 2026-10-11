from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from crypto_trader.fills import bar_exit
from crypto_trader.models import Bar, ExitReason, Position, PositionStatus


def _pos(stop: str, target: str) -> Position:
    return Position(
        id=1,
        symbol="BTC-USD",
        qty=Decimal("0.01"),
        entry_price=Decimal("100"),
        stop=Decimal(stop),
        target=Decimal(target),
        opened_at=datetime(2026, 3, 9, 15, 0, tzinfo=UTC),
        entry_fee=Decimal("0.10"),
        cost_basis=Decimal("1.10"),
        status=PositionStatus.OPEN,
    )


def test_stop_wins_when_bar_touches_both():
    bar = Bar(
        ts=datetime(2026, 3, 9, 15, 5, tzinfo=UTC),
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal("105"),
    )
    fill = bar_exit(bar, _pos("95", "108"), slippage_bps=10)
    assert fill is not None
    assert fill.reason is ExitReason.STOP
    assert fill.price < Decimal("95")


def test_target_fill_includes_slippage():
    bar = Bar(
        ts=datetime(2026, 3, 9, 15, 5, tzinfo=UTC),
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("99"),
        close=Decimal("109"),
    )
    fill = bar_exit(bar, _pos("90", "108"), slippage_bps=10)
    assert fill is not None
    assert fill.reason is ExitReason.TARGET
    assert fill.price < Decimal("108")
