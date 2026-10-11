from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from crypto_trader.models import Bar, Trade
from crypto_trader.money import D, money


@dataclass
class Report:
    trades: int
    wins: int
    losses: int
    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    expectancy: Decimal
    max_drawdown: Decimal
    total_fees: Decimal
    total_pnl: Decimal
    buy_hold_pnl: Decimal | None


def trade_report(trades: list[Trade], bars: list[Bar] | None = None, stake: Decimal | None = None) -> Report:
    if not trades:
        bh = _buy_hold(bars, stake) if bars and stake else None
        return Report(0, 0, 0, Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), bh)
    pnls = [D(t.pnl) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    avg_win = money(sum(wins) / len(wins)) if wins else Decimal("0")
    avg_loss = money(abs(sum(losses) / len(losses))) if losses else Decimal("0")
    win_rate = D(len(wins)) / D(len(pnls))
    expectancy = money(win_rate * avg_win - (1 - win_rate) * avg_loss)
    equity = Decimal("0")
    peak = Decimal("0")
    max_dd = Decimal("0")
    for p in pnls:
        equity += p
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > max_dd:
            max_dd = dd
    fees = money(sum((D(t.entry_fee) + D(t.exit_fee) for t in trades), Decimal("0")))
    return Report(
        trades=len(trades),
        wins=len(wins),
        losses=len(losses),
        win_rate=money(win_rate, Decimal("0.0001")),
        avg_win=avg_win,
        avg_loss=avg_loss,
        expectancy=expectancy,
        max_drawdown=money(max_dd),
        total_fees=fees,
        total_pnl=money(sum(pnls, Decimal("0"))),
        buy_hold_pnl=_buy_hold(bars, stake) if bars and stake else None,
    )


def _buy_hold(bars: list[Bar], stake: Decimal) -> Decimal | None:
    if len(bars) < 2 or bars[0].open <= 0:
        return None
    qty = stake / bars[0].open
    return money((bars[-1].close - bars[0].open) * qty)


def trades_to_csv(trades: list[Trade]) -> str:
    header = (
        "id,opened_at,closed_at,symbol,side,qty,entry_price,exit_price,"
        "entry_fee,exit_fee,pnl,cost_basis,reason,mode"
    )
    lines = [header]
    for t in trades:
        lines.append(
            ",".join(
                [
                    str(t.id or ""),
                    t.opened_at.isoformat(),
                    t.closed_at.isoformat(),
                    t.symbol,
                    t.side,
                    str(t.qty),
                    str(t.entry_price),
                    str(t.exit_price),
                    str(t.entry_fee),
                    str(t.exit_fee),
                    str(t.pnl),
                    str(t.cost_basis),
                    t.reason,
                    t.mode,
                ]
            )
        )
    return "\n".join(lines) + "\n"
