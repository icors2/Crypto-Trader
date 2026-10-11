from __future__ import annotations

from decimal import Decimal

from crypto_trader.models import Bar, Indicators
from crypto_trader.money import D


def ema(values: list[Decimal], period: int) -> list[Decimal | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[Decimal | None] = [None] * len(values)
    if len(values) < period:
        return out
    seed = sum(values[:period], Decimal("0")) / Decimal(period)
    out[period - 1] = seed
    k = Decimal(2) / Decimal(period + 1)
    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def true_range(bars: list[Bar]) -> list[Decimal]:
    trs: list[Decimal] = []
    prev_close: Decimal | None = None
    for bar in bars:
        high_low = bar.high - bar.low
        if prev_close is None:
            trs.append(high_low)
        else:
            trs.append(max(high_low, abs(bar.high - prev_close), abs(bar.low - prev_close)))
        prev_close = bar.close
    return trs


def atr(bars: list[Bar], period: int) -> list[Decimal | None]:
    trs = true_range(bars)
    out: list[Decimal | None] = [None] * len(bars)
    if len(trs) < period:
        return out
    first = sum(trs[:period], Decimal("0")) / Decimal(period)
    out[period - 1] = first
    prev = first
    for i in range(period, len(trs)):
        prev = (prev * (period - 1) + trs[i]) / Decimal(period)
        out[i] = prev
    return out


def compute_indicators(
    bars: list[Bar],
    *,
    ema_fast: int,
    ema_slow: int,
    atr_period: int,
    htf_bars: list[Bar] | None = None,
    htf_ema_period: int = 50,
) -> Indicators | None:
    if len(bars) < max(ema_slow, atr_period) + 1:
        return None
    closes = [D(b.close) for b in bars]
    fast = ema(closes, ema_fast)
    slow = ema(closes, ema_slow)
    atrs = atr(bars, atr_period)
    if fast[-1] is None or slow[-1] is None or atrs[-1] is None:
        return None
    if fast[-2] is None or slow[-2] is None:
        return None
    htf_ema_val: Decimal | None = None
    htf_close: Decimal | None = None
    if htf_bars:
        htf_closes = [D(b.close) for b in htf_bars]
        htf_series = ema(htf_closes, htf_ema_period)
        if htf_series[-1] is not None:
            htf_ema_val = htf_series[-1]
            htf_close = htf_closes[-1]
    return Indicators(
        ema_fast=fast[-1],
        ema_slow=slow[-1],
        atr=atrs[-1],
        prev_ema_fast=fast[-2],
        prev_ema_slow=slow[-2],
        htf_ema=htf_ema_val,
        htf_close=htf_close,
    )
