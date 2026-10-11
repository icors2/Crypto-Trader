from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from crypto_trader.models import Bar, ExitReason, Position, Quote
from crypto_trader.money import apply_bps


@dataclass(frozen=True)
class ExitFill:
    reason: ExitReason
    price: Decimal


def bar_exit(bar: Bar, position: Position, slippage_bps: int) -> ExitFill | None:
    """If a bar touches stop and target, the stop is assumed to have hit first."""
    stop_hit = bar.low <= position.stop
    target_hit = bar.high >= position.target
    if stop_hit:
        fill = apply_bps(position.stop, slippage_bps, adverse=True)
        # Long exit: adverse is a worse (lower) sale. apply_bps(adverse=True) raises.
        fill = apply_bps(position.stop, slippage_bps, adverse=False)
        return ExitFill(ExitReason.STOP, fill)
    if target_hit:
        fill = apply_bps(position.target, slippage_bps, adverse=False)
        return ExitFill(ExitReason.TARGET, fill)
    return None


def quote_exit(quote: Quote, position: Position, slippage_bps: int) -> ExitFill | None:
    if quote.bid <= position.stop:
        return ExitFill(ExitReason.STOP, apply_bps(position.stop, slippage_bps, adverse=False))
    if quote.bid >= position.target:
        return ExitFill(ExitReason.TARGET, apply_bps(position.target, slippage_bps, adverse=False))
    return None


def paper_buy_fill(ask: Decimal, slippage_bps: int) -> Decimal:
    return apply_bps(ask, slippage_bps, adverse=True)


def paper_sell_fill(bid: Decimal, slippage_bps: int) -> Decimal:
    return apply_bps(bid, slippage_bps, adverse=False)
