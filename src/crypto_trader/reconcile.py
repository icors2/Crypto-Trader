from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from crypto_trader.db import Database
from crypto_trader.models import Order, OrderStatus, Position, PositionStatus
from crypto_trader.money import D, money
from crypto_trader.paper import PaperBroker
from crypto_trader.timeutil import now_utc


@dataclass
class ReconcileResult:
    confirmed: list[str]
    mismatches: list[str]
    dust: list[str]


def is_dust(qty: Decimal, price: Decimal, min_order_size: Decimal, dust_notional: Decimal) -> bool:
    if qty <= 0:
        return False
    if qty < min_order_size:
        return True
    return qty * price < dust_notional


def reconcile_pending(
    db: Database,
    lookup,
    *,
    min_order_size: Decimal,
    dust_notional: Decimal,
    mark_price: Decimal | None = None,
) -> ReconcileResult:
    """Look up stored client_order_id values that were not confirmed (crash after POST)."""
    confirmed: list[str] = []
    mismatches: list[str] = []
    dust: list[str] = []
    for pending in db.pending_orders():
        found: Order | None = lookup(pending.client_order_id)
        if found is None:
            mismatches.append(f"missing:{pending.client_order_id}")
            continue
        db.upsert_order(found)
        confirmed.append(pending.client_order_id)
        if found.status in {OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED} and found.filled_qty > 0:
            existing = db.open_position()
            if existing is None and found.side.value == "buy" and found.average_price:
                price = found.average_price
                qty = found.filled_qty
                px = mark_price or price
                status = PositionStatus.DUST if is_dust(qty, px, min_order_size, dust_notional) else PositionStatus.OPEN
                if status is PositionStatus.DUST:
                    dust.append(pending.client_order_id)
                db.insert_position(
                    Position(
                        id=None,
                        symbol=found.symbol,
                        qty=qty,
                        entry_price=price,
                        stop=price,
                        target=price,
                        opened_at=found.submitted_at or now_utc(),
                        entry_fee=found.fee_charged,
                        cost_basis=money(price * qty + found.fee_charged),
                        status=status,
                        client_order_id=found.client_order_id,
                    )
                )
            elif existing and found.side.value == "buy":
                if D(existing.qty) != D(found.filled_qty):
                    mismatches.append(f"qty:{pending.client_order_id}")
        if found.status is OrderStatus.PARTIALLY_FILLED:
            qty = found.filled_qty
            px = mark_price or found.average_price or Decimal("0")
            if is_dust(qty, px, min_order_size, dust_notional):
                dust.append(pending.client_order_id)
    return ReconcileResult(confirmed, mismatches, dust)


def paper_lookup(broker: PaperBroker):
    def _lookup(client_order_id: str) -> Order | None:
        return broker.get_order(client_order_id)

    return _lookup
