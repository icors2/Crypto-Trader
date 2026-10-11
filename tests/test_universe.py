from __future__ import annotations

import pytest

from crypto_trader.config import BotConfig, load_config, save_config, validate_config
from crypto_trader.universe import (
    normalize_symbol,
    pairs_from_robinhood,
    parse_symbols,
    resolve_universe,
)


def test_normalize_and_parse_symbols():
    assert normalize_symbol("eth") == "ETH-USD"
    assert normalize_symbol("sol-usd") == "SOL-USD"
    assert parse_symbols("BTC-USD, ETH, doge-usd") == ["BTC-USD", "ETH-USD", "DOGE-USD"]
    assert parse_symbols(["XRP-USD", "XRP-USD", "sol"]) == ["XRP-USD", "SOL-USD"]
    with pytest.raises(ValueError):
        normalize_symbol("???")


def test_watchlist_falls_back_to_symbol(env_settings):
    cfg = validate_config(BotConfig(symbol="ETH-USD", symbols=[]), env_settings)
    assert cfg.watchlist() == ["ETH-USD"]
    assert cfg.symbol == "ETH-USD"


def test_watchlist_from_yaml_list(env_settings):
    save_config(
        env_settings.config_path,
        {"symbols": ["SOL-USD", "DOGE-USD"], "max_open_positions": 3},
        env_settings,
    )
    loaded = load_config(env_settings.config_path, env_settings)
    assert loaded.watchlist() == ["SOL-USD", "DOGE-USD"]
    assert loaded.symbol == "SOL-USD"
    assert loaded.max_open_positions == 3


def test_robinhood_rows_filter_non_usd_and_untradable():
    rows = [
        {"symbol": "ETH-USD", "asset_code": "ETH", "quote_code": "USD", "status": "tradable", "is_api_tradable": True},
        {"symbol": "BTC-USD", "asset_code": "BTC", "quote_code": "USD", "status": "sellonly", "is_api_tradable": True},
        {"symbol": "EURC-USD", "asset_code": "EURC", "quote_code": "USD", "status": "tradable", "is_api_tradable": False},
        {"symbol": "BTC-EUR", "asset_code": "BTC", "quote_code": "EUR", "status": "tradable", "is_api_tradable": True},
    ]
    pairs = pairs_from_robinhood(rows)
    assert [p.symbol for p in pairs] == ["ETH-USD"]


def test_resolve_universe_intersects_coinbase():
    rows = [
        {"symbol": "WIF-USD", "asset_code": "WIF", "quote_code": "USD", "status": "tradable", "is_api_tradable": True},
        {"symbol": "NOPE-USD", "asset_code": "NOPE", "quote_code": "USD", "status": "tradable", "is_api_tradable": True},
    ]
    pairs = resolve_universe(robinhood_rows=rows, coinbase_ids={"WIF-USD", "BTC-USD"})
    assert [p.symbol for p in pairs] == ["WIF-USD"]
