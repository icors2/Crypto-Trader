---
name: run-backtest
description: Run the Coinbase-candle EMA/ATR backtest and report expectancy versus buy-and-hold. Use when evaluating strategy changes or the go-live bar.
---

# Run backtest

## When to use

- After changing EMA/ATR/fee/slippage settings
- When comparing paper results to the historical path

## Preconditions

- `uv sync --all-extras`
- Network access to Coinbase Exchange public candles, or a fixture

## Steps

1. Confirm `config/config.yaml` is the intended parameter set (`fee_bps` must not be 0).
2. Run `uv run crypto-trader backtest --limit 300`.
3. Record expectancy, average win/loss, max drawdown, total fees, and buy-and-hold.
4. If live quotes are being paper-traded, compare those extras to this report before flipping `mode: live`.

## Verify

- Output is JSON with a non-null `trades` count (may be 0 on a quiet window).
- Fees are > 0 whenever a trade exists.

## Failure modes

- Coinbase 429: wait and retry; do not fall back to sampled mid bars.
- Missing tzdata: install the `tzdata` package (Docker image already does).
