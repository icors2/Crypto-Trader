from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

# Robinhood Crypto USD pairs that typically also have Coinbase Exchange candles.
# Live mode refreshes from GET /api/v2/crypto/trading/trading_pairs/.
# Paper mode uses this catalog (intersected with Coinbase products when reachable).
ROBINHOOD_USD_PAIRS: tuple[str, ...] = (
    "AAVE-USD",
    "ADA-USD",
    "ALGO-USD",
    "APT-USD",
    "ARB-USD",
    "ATOM-USD",
    "AVAX-USD",
    "AXS-USD",
    "BCH-USD",
    "BONK-USD",
    "BTC-USD",
    "COMP-USD",
    "CRV-USD",
    "DOGE-USD",
    "DOT-USD",
    "ENS-USD",
    "ETC-USD",
    "ETH-USD",
    "FET-USD",
    "FIL-USD",
    "FLOKI-USD",
    "GRT-USD",
    "HBAR-USD",
    "IMX-USD",
    "INJ-USD",
    "JUP-USD",
    "LDO-USD",
    "LINK-USD",
    "LTC-USD",
    "MANA-USD",
    "MKR-USD",
    "NEAR-USD",
    "ONDO-USD",
    "OP-USD",
    "PEPE-USD",
    "POL-USD",
    "PYTH-USD",
    "QNT-USD",
    "RENDER-USD",
    "SAND-USD",
    "SEI-USD",
    "SHIB-USD",
    "SOL-USD",
    "STX-USD",
    "SUI-USD",
    "TIA-USD",
    "UNI-USD",
    "VET-USD",
    "WIF-USD",
    "XLM-USD",
    "XRP-USD",
    "XTZ-USD",
)


@dataclass(frozen=True)
class TradingPair:
    symbol: str
    asset_code: str
    quote_code: str = "USD"
    min_order_amount: str | None = None
    is_api_tradable: bool = True
    source: str = "catalog"


def normalize_symbol(raw: str) -> str:
    ticker = raw.strip().upper().replace("/", "-").replace("_", "-")
    if not ticker:
        raise ValueError("symbol is empty")
    if "-" not in ticker:
        ticker = f"{ticker}-USD"
    base, _, quote = ticker.partition("-")
    if not base or not quote or not base.isalnum() or not quote.isalpha():
        raise ValueError(f"symbol must look like BTC-USD, got {raw!r}")
    return f"{base}-{quote}"


def parse_symbols(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple, set)):
        items: Iterable[Any] = value
    else:
        items = str(value).replace("\n", ",").split(",")
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        symbol = normalize_symbol(text)
        if symbol not in seen:
            seen.add(symbol)
            out.append(symbol)
    return out


def catalog_pairs() -> list[TradingPair]:
    return [
        TradingPair(symbol=symbol, asset_code=symbol.split("-")[0], source="catalog")
        for symbol in ROBINHOOD_USD_PAIRS
    ]


def pairs_from_robinhood(rows: list[dict[str, Any]]) -> list[TradingPair]:
    out: list[TradingPair] = []
    seen: set[str] = set()
    for row in rows:
        status = str(row.get("status") or "").lower()
        if status and status not in {"tradable"}:
            continue
        if row.get("is_api_tradable") is False:
            continue
        quote = str(row.get("quote_code") or "USD").upper()
        if quote != "USD":
            continue
        try:
            symbol = normalize_symbol(str(row.get("symbol") or ""))
        except ValueError:
            continue
        if symbol in seen:
            continue
        seen.add(symbol)
        out.append(
            TradingPair(
                symbol=symbol,
                asset_code=str(row.get("asset_code") or symbol.split("-")[0]).upper(),
                quote_code=quote,
                min_order_amount=str(row.get("min_order_amount")) if row.get("min_order_amount") else None,
                is_api_tradable=True,
                source="robinhood",
            )
        )
    return out


def intersect_coinbase(pairs: list[TradingPair], coinbase_ids: set[str] | None) -> list[TradingPair]:
    if not coinbase_ids:
        return pairs
    return [pair for pair in pairs if pair.symbol in coinbase_ids]


def resolve_universe(
    *,
    robinhood_rows: list[dict[str, Any]] | None = None,
    coinbase_ids: set[str] | None = None,
) -> list[TradingPair]:
    pairs = pairs_from_robinhood(robinhood_rows) if robinhood_rows else catalog_pairs()
    return intersect_coinbase(pairs, coinbase_ids)
