from __future__ import annotations

from decimal import Decimal

from crypto_trader.config import BotConfig
from crypto_trader.models import Indicators, Quote, Signal
from crypto_trader.money import D, round_trip_cost_per_unit, spread_bps


def bullish_cross(ind: Indicators) -> bool:
    return ind.prev_ema_fast <= ind.prev_ema_slow and ind.ema_fast > ind.ema_slow


def evaluate_entry(
    cfg: BotConfig,
    ind: Indicators,
    quote: Quote,
    *,
    cooldown_remaining: int = 0,
) -> Signal:
    if cooldown_remaining > 0:
        return Signal(False, f"cooldown:{cooldown_remaining}")
    if not bullish_cross(ind):
        return Signal(False, "no_cross")
    spr = spread_bps(quote.bid, quote.ask)
    if spr > D(cfg.spread_max_bps):
        return Signal(False, f"spread:{spr:.2f}")
    target_distance = ind.atr * D(cfg.target_atr_mult)
    rtc = round_trip_cost_per_unit(quote.mid, quote.spread, cfg.fee_bps)
    need = rtc * D(cfg.cost_multiple)
    if target_distance <= need:
        return Signal(False, f"cost_unaware: target {target_distance} < need {need}")
    if cfg.htf_filter_enabled:
        if ind.htf_ema is None or ind.htf_close is None:
            return Signal(False, "htf_unavailable")
        if ind.htf_close <= ind.htf_ema:
            return Signal(False, "htf_downtrend")
    return Signal(True, None)


def position_exits(
    entry: Decimal,
    atr_value: Decimal,
    cfg: BotConfig,
) -> tuple[Decimal, Decimal]:
    stop = entry - atr_value * D(cfg.stop_atr_mult)
    target = entry + atr_value * D(cfg.target_atr_mult)
    return stop, target
