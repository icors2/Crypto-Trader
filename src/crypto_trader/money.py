from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Any

TWOPLACE = Decimal("0.01")
BPS = Decimal("10000")


def D(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        raise ValueError("cannot convert None to Decimal")
    return Decimal(str(value))


def money(value: Any, places: Decimal = TWOPLACE) -> Decimal:
    return D(value).quantize(places, rounding=ROUND_HALF_UP)


def qty(value: Any, places: Decimal = Decimal("0.00000001")) -> Decimal:
    return D(value).quantize(places, rounding=ROUND_DOWN)


def bps_to_frac(bps: int | Decimal) -> Decimal:
    return D(bps) / BPS


def apply_bps(price: Decimal, bps: int | Decimal, *, adverse: bool) -> Decimal:
    frac = bps_to_frac(bps)
    return price * (1 + frac) if adverse else price * (1 - frac)


def spread_bps(bid: Decimal, ask: Decimal) -> Decimal:
    mid = (bid + ask) / 2
    if mid <= 0:
        raise ValueError("mid price must be positive")
    return ((ask - bid) / mid) * BPS


def fee_amount(notional: Decimal, fee_bps: int | Decimal) -> Decimal:
    return money(notional * bps_to_frac(fee_bps))


def round_trip_cost_per_unit(
    mid: Decimal,
    spread: Decimal,
    fee_bps: int | Decimal,
) -> Decimal:
    """Estimated all-in cost of a round trip per 1 unit of asset."""
    fee_each = mid * bps_to_frac(fee_bps)
    return spread + (fee_each * 2)
