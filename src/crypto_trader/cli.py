from __future__ import annotations

import argparse
import json
import sys

from crypto_trader.adapters.coinbase import CoinbaseFeed
from crypto_trader.backtest import run_backtest
from crypto_trader.config import load_config
from crypto_trader.settings import EnvSettings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="crypto-trader")
    sub = parser.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="run the web UI and trading loop")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    bt = sub.add_parser("backtest", help="run a Coinbase-candle backtest")
    bt.add_argument("--symbol", default=None)
    bt.add_argument("--limit", type=int, default=300)

    live = sub.add_parser("live-check", help="read-only Robinhood account call")
    live.add_argument(
        "--place-min",
        action="store_true",
        help="reserved; still requires a manual Robinhood-app check",
    )

    args = parser.parse_args(argv)
    settings = EnvSettings()
    cfg = load_config(settings.config_path, settings)

    if args.cmd == "serve":
        import uvicorn

        host = args.host or settings.bind_host
        port = args.port or settings.port
        uvicorn.run("crypto_trader.app:app", host=host, port=port, factory=False)
        return 0

    if args.cmd == "backtest":
        symbol = args.symbol or cfg.symbol
        feed = CoinbaseFeed()
        bars = feed.get_candles(symbol, cfg.timeframe_seconds, limit=args.limit)
        htf = (
            feed.get_candles(symbol, cfg.htf_timeframe_seconds, limit=200)
            if cfg.htf_filter_enabled
            else None
        )
        result = run_backtest(bars, cfg, htf)
        print(json.dumps(result.report.__dict__, default=str, indent=2))
        return 0

    if args.cmd == "live-check":
        if not settings.robinhood_api_key or not settings.robinhood_private_key:
            print("Set ROBINHOOD_API_KEY and ROBINHOOD_PRIVATE_KEY", file=sys.stderr)
            return 2
        from crypto_trader.adapters.robinhood import RobinhoodClient

        client = RobinhoodClient(
            settings.robinhood_api_key,
            settings.robinhood_private_key,
            settings.robinhood_account_number,
        )
        accounts = client.get_accounts()
        print(json.dumps(accounts, indent=2, default=str))
        warn = client.startup_clock_warning()
        if warn:
            print(warn, file=sys.stderr)
        if args.place_min:
            print(
                "Do the minimum-size round trip in the Robinhood app after this read-only check.",
                file=sys.stderr,
            )
            return 3
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
