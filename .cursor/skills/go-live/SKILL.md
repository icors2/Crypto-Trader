---
name: go-live
description: Gate flipping the bot from paper to live Robinhood v2. Use when the operator asks to enable live trading.
---

# Go live

Do not flip `mode: live` because a single paper day looked good.

## Preconditions (the go-live bar)

1. At least 4 weeks of paper trading **on live Robinhood quotes** (Coinbase candles for indicators).
2. At least 30 paper trades.
3. Paper expectancy has the same sign as the Coinbase backtest, and is not wildly better (paper overstating live is the main risk).
4. `fee_bps` has been calibrated from logged `fee_charged` / `estimated_price`.
5. `/healthz` has stayed healthy; no silent loop deaths.

## First live run

1. `uv run crypto-trader live-check` — read-only accounts call. Confirm clock-skew warning is absent.
2. Place **one** minimum-size round trip by hand and verify it in the Robinhood app.
3. Only then set `mode: live` in `config/config.yaml` (or the settings page). Hard ceilings in `.env` still apply.
4. Watch ntfy/Discord-equivalent alerts for halt, restart, and quote failures.

## Accepted risk

Bot-managed stops only work while the process, VM, and network are up. At $100 notional this is accepted; there is no exchange `stop_loss` backstop in v1.

## Gemini

Do not add a Gemini news filter. It was cut from v1.

## Failure modes

- Missing `ROBINHOOD_ACCOUNT_NUMBER` — v2 orders require it.
- STOP file left in `data/STOP` — loop stays paused.
- Weekly/cumulative halt — needs the Resume button, not a container restart.
