from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from crypto_trader.config import BotConfig
from crypto_trader.fills import bar_exit
from crypto_trader.indicators import compute_indicators
from crypto_trader.models import Bar, Position, PositionStatus, Quote, Trade
from crypto_trader.money import D, fee_amount, money
from crypto_trader.reports import Report, trade_report
from crypto_trader.strategy import evaluate_entry, position_exits


@dataclass
class BacktestResult:
    trades: list[Trade]
    report: Report


def run_backtest(bars: list[Bar], cfg: BotConfig, htf_bars: list[Bar] | None = None) -> BacktestResult:
    trades: list[Trade] = []
    position: Position | None = None
    cooldown = 0
    last_stop_bar_index = -10_000

    for i in range(1, len(bars)):
        hist = bars[: i + 1]
        closed = hist[:-1]
        if len(closed) < cfg.ema_slow + 2:
            continue
        htf = None
        if cfg.htf_filter_enabled and htf_bars:
            htf = [b for b in htf_bars if b.ts <= closed[-1].ts]
        ind = compute_indicators(
            closed,
            ema_fast=cfg.ema_fast,
            ema_slow=cfg.ema_slow,
            atr_period=cfg.atr_period,
            htf_bars=htf,
            htf_ema_period=cfg.htf_ema_period,
        )
        if ind is None:
            continue
        bar = bars[i]
        if position:
            fill = bar_exit(bar, position, cfg.slippage_bps)
            held = (bar.ts - position.opened_at) >= timedelta(minutes=cfg.max_hold_minutes)
            if fill or held:
                exit_price = fill.price if fill else bar.close
                reason = fill.reason.value if fill else "max_hold"
                exit_fee = fee_amount(exit_price * position.qty, cfg.fee_bps)
                pnl = money((exit_price - position.entry_price) * position.qty - position.entry_fee - exit_fee)
                trades.append(
                    Trade(
                        id=len(trades) + 1,
                        opened_at=position.opened_at,
                        closed_at=bar.ts,
                        symbol=cfg.symbol,
                        side="long",
                        qty=position.qty,
                        entry_price=position.entry_price,
                        exit_price=exit_price,
                        entry_fee=position.entry_fee,
                        exit_fee=exit_fee,
                        pnl=pnl,
                        cost_basis=position.cost_basis,
                        reason=reason,
                        mode="backtest",
                    )
                )
                if reason == "stop":
                    last_stop_bar_index = i
                position = None
            continue

        cooldown = max(0, cfg.cooldown_bars - (i - last_stop_bar_index))
        quote = Quote(ts=bar.ts, symbol=cfg.symbol, bid=bar.open, ask=bar.open, source="ohlc")
        signal = evaluate_entry(cfg, ind, quote, cooldown_remaining=cooldown)
        if not signal.enter_long:
            continue
        entry = bar.open
        qty = (D(cfg.max_notional_usd) / entry).quantize(Decimal("0.00000001"))
        fee = fee_amount(entry * qty, cfg.fee_bps)
        stop, target = position_exits(entry, ind.atr, cfg)
        position = Position(
            id=None,
            symbol=cfg.symbol,
            qty=qty,
            entry_price=entry,
            stop=stop,
            target=target,
            opened_at=bar.ts,
            entry_fee=fee,
            cost_basis=money(entry * qty + fee),
            status=PositionStatus.OPEN,
        )
    report = trade_report(trades, bars, D(cfg.max_notional_usd))
    return BacktestResult(trades=trades, report=report)
