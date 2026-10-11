# Crypto day-trader bot: plan review

Oct 10, 2026 · @Chris O'Neal

## Overview

The plan is sound: paper-by-default, deterministic risk limits, no unofficial libraries and clear Docker halt semantics. The main risks are paper results that overstate live performance, and a bot that fails silently while the container looks healthy.

Below are changes and additions, most important first. The Robinhood v2 field names have not been checked against their current docs, so verify the API details before the live phase.

## Fix before building

Eight issues change how the bot behaves or how far its results can be trusted.

1. **Fee modeling contradicts itself.** The API notes say v2 `bid`/`ask` exclude the fee, but the paper section sets `fee_bps` to 0 because "the spread is already in the quote." If the fee is separate, paper mode understates costs on every trade. Default it to your actual fee tier, and log a few days of real `fee_charged` and estimated-price data to calibrate.
2. **Indicators differ between backtest and live.** The backtest uses true Coinbase OHLC. Live builds bars from mid-price sampled every 15s, which misses intrabar highs and lows, so live ATR runs smaller than backtest ATR and live stops end up tighter than the ones you tested. The seam between Coinbase seed history and sampled bars also skews EMA warm-up. Either use Coinbase candles for indicators in both modes and Robinhood quotes only for fills and exits, or build sampled bars in both. Also record the Robinhood bid/ask series to SQLite from day one, so you eventually have a real spread dataset to backtest against.
3. **Backtest stop/target ordering.** When one bar's range touches both stop and target, assume the stop hit first. Fill at the stop price plus slippage, not at a perfect level.
4. **The daily loss halt resets every day.** A bot that loses $50 daily keeps running indefinitely. Add a cumulative or weekly loss cap that requires a manual resume, and count unrealized loss in the daily check too.
5. **The trading thread can die silently.** Uvicorn keeps serving while the trading thread is dead, so the container looks healthy and positions go unmanaged. Add a heartbeat the loop updates every pass, plus a Docker `HEALTHCHECK` and `/healthz` that fails when it goes stale. Treat unexpected loop exceptions as fatal (exit, so `restart: unless-stopped` recovers) and distinguish them from the deliberate paused state.
6. **Single-file bind mount of `config.yaml`.** Atomic writes (temp file plus rename) fail or detach on a single-file Docker bind mount. Mount a `./config/` directory instead. Rewriting the YAML will also drop comments.
7. **`tzdata` is missing from slim images.** `python:slim` lacks it, so `zoneinfo("America/Chicago")` fails. Add the `tzdata` package, and include a DST-transition day in the Chicago halt tests.
8. **A compromised or mistaken UI shouldn't be able to raise its own limits.** Add hard ceilings from `.env` (for example `MAX_NOTIONAL_USD`) that the form can't exceed, and range-validate every field (fast < slow EMA, positive multipliers, sane poll interval). Keep an audit table of config changes in SQLite.

## Live-mode gaps

Live trading adds failure modes that paper mode never exercises.

- **Startup reconciliation.** Compare local positions against Robinhood holdings and open orders. On restart, look up any order whose `client_order_id` was stored but not confirmed, since the crash window between POST and fill is the dangerous one.
- **Stuck dust.** A position below `min_order_size` after partial fills or rounding can't be sold. Define what happens: alert, leave it, or mark it dust.
- **Stale or failed quotes.** After N failed polls or a stale quote, block entries and alert, and add 429 backoff with jitter. Right now only the Gemini path is explicitly fail-safe.
- **No exchange-side backstop.** Bot-managed stops only work while the process, VM and network are up. At $100 sizing that is tolerable, but consider an exchange `stop_loss` order as a backstop, or document it as an accepted risk.
- **Alerts.** Nothing tells you when a halt, repeated errors or an unexpected restart happens. A push to ntfy, Discord or Telegram is a small addition.
- **Clock skew.** Check against the API's response `Date` header at startup and warn if it is off by more than a few seconds. VM suspend or migration can cause drift even with NTP.
- **First live run.** Do a read-only account call, then one minimum-size round trip, with manual verification in the Robinhood app, before enabling the loop.

## Strategy additions

These are cheap to add and filter out the trades most likely to lose to costs.

- **Spread filter on entry.** You already get bid and ask, so skip entries when the spread exceeds X bps.
- **Cost-aware entries.** Require the ATR target distance to exceed some multiple of estimated round-trip cost, otherwise skip.
- **Cooldown and max hold time.** A cooldown after a stop-out and a maximum hold time both reduce whipsaw churn.
- **Optional higher-timeframe trend filter**, for example price above a 1h EMA.
- **A go-live bar in the README.** For example: N weeks of paper on live quotes, a minimum trade count, and paper results consistent with the backtest. Without it, "flip the flag" becomes a mood decision.
- **Report extras.** Expectancy, average win and loss, max drawdown, total fees, and a buy-and-hold benchmark. A 5m EMA cross on fee-bearing crypto often loses after costs, so the benchmark tells you whether the bot is doing anything.

## Web UI and ops

The settings page can change trading behavior, so it deserves the same care as the broker client.

- **Transport.** Don't serve plaintext HTTP on `0.0.0.0` if you can avoid it. If the VM is on Tailscale, bind to that interface or use `tailscale serve` for HTTPS. Otherwise `Secure` cookies can't work.
- **Auth.** Use `SameSite=Strict` and session expiry. Add login rate limiting, a constant-time compare, and ideally a password hash instead of a plaintext `UI_PASSWORD`.
- **STOP file location.** Put it under `./data/` so it is reachable from the host through the volume.
- **Number handling.** Use Decimal end to end, and store prices and quantities in SQLite as TEXT, not REAL.
- **SQLite concurrency.** The trading thread and web threads share the database, so use WAL mode, one connection per thread and a write lock. Back it up via `sqlite3 .backup` or Proxmox VM backups.
- **Container hygiene.** Run as a non-root user, add log rotation (`max-size` and `max-file`), and commit `uv.lock`.
- **Stored exits.** Store each open position's stop and target at entry and don't recompute them on config hot-reload. Otherwise saving settings mid-trade silently changes live exits.
- **Verify script.** The `tests-docs` todo mentions `npm run verify`. Confirm that script actually runs `ruff` and `pytest` in this starter.

## Extra tests

Add these to the existing pytest list; each one covers a failure mode introduced or exposed above.

- Crash between order POST and fill, then restart reconciliation
- Partial fill
- Stale quote blocks entry
- 429 backoff
- Config hot-reload with an open position leaves its stop and target unchanged
- Spread-filter skip
- Clock-skew warning
- Dead trading thread makes the healthcheck fail
- Chicago halt across a DST transition day

## Scope and tax

Cut the Gemini filter from v1. It is off by default and adds a key, a network dependency and extra test surface without improving the core.

In the US each round trip is a taxable disposal. Have the trade CSV include fees and cost basis, since reconciling many small trades against Robinhood's year-end forms is painful. This is not tax advice, so confirm the details with a tax professional.
