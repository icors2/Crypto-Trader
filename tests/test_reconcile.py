from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from crypto_trader.db import Database
from crypto_trader.models import Order, OrderStatus, Side
from crypto_trader.paper import PaperBroker
from crypto_trader.reconcile import reconcile_pending


def test_crash_between_post_and_fill_reconciles(tmp_path):
    db = Database(tmp_path / "t.db")
    broker = PaperBroker(fee_bps=100)
    pending = Order(
        client_order_id="11111111-1111-1111-1111-111111111111",
        symbol="BTC-USD",
        side=Side.BUY,
        qty=Decimal("0.01"),
        status=OrderStatus.PENDING,
        submitted_at=datetime(2026, 3, 9, tzinfo=UTC),
    )
    db.upsert_order(pending)
    broker.orders[pending.client_order_id] = Order(
        client_order_id=pending.client_order_id,
        symbol="BTC-USD",
        side=Side.BUY,
        qty=Decimal("0.01"),
        filled_qty=Decimal("0.01"),
        average_price=Decimal("100"),
        fee_charged=Decimal("0.10"),
        status=OrderStatus.FILLED,
        submitted_at=pending.submitted_at,
    )
    result = reconcile_pending(
        db,
        broker.get_order,
        min_order_size=Decimal("0.0001"),
        dust_notional=Decimal("1"),
        mark_price=Decimal("100"),
    )
    assert pending.client_order_id in result.confirmed
    pos = db.open_position()
    assert pos is not None
    assert pos.qty == Decimal("0.01")


def test_partial_fill_marked_dust_when_too_small(tmp_path):
    db = Database(tmp_path / "t.db")
    pending = Order(
        client_order_id="22222222-2222-2222-2222-222222222222",
        symbol="BTC-USD",
        side=Side.BUY,
        qty=Decimal("1"),
        status=OrderStatus.PENDING,
        submitted_at=datetime(2026, 3, 9, tzinfo=UTC),
    )
    db.upsert_order(pending)

    def lookup(_cid: str) -> Order:
        return Order(
            client_order_id=pending.client_order_id,
            symbol="BTC-USD",
            side=Side.BUY,
            qty=Decimal("1"),
            filled_qty=Decimal("0.0000001"),
            average_price=Decimal("100"),
            fee_charged=Decimal("0"),
            status=OrderStatus.PARTIALLY_FILLED,
            submitted_at=pending.submitted_at,
        )

    result = reconcile_pending(
        db,
        lookup,
        min_order_size=Decimal("0.001"),
        dust_notional=Decimal("1"),
        mark_price=Decimal("100"),
    )
    assert pending.client_order_id in result.dust
    pos = db.open_position()
    assert pos is None or pos.status.value == "dust"
