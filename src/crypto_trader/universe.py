from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

# Robinhood Crypto USD pairs (US app availability, Oct 2026).
# Source of truth when keyed: GET /api/v2/crypto/trading/trading_pairs/
# (is_api_tradable + status=tradable). Coinbase is never used to hide a pair.
_STABLE = {"USD", "USDC", "USDG"}

ROBINHOOD_USD_PAIRS: tuple[str, ...] = (
    "AAVE-USD",
    "ADA-USD",
    "AERO-USD",
    "ALGO-USD",
    "ARB-USD",
    "ASTER-USD",
    "ATOM-USD",
    "AVAX-USD",
    "AVNT-USD",
    "AXS-USD",
    "BAT-USD",
    "BCH-USD",
    "BILL-USD",
    "BIO-USD",
    "BNB-USD",
    "BONK-USD",
    "BTC-USD",
    "CC-USD",
    "COMP-USD",
    "CRV-USD",
    "DOGE-USD",
    "DOT-USD",
    "EIGEN-USD",
    "ENA-USD",
    "ETC-USD",
    "ETH-USD",
    "FET-USD",
    "FLOKI-USD",
    "FLR-USD",
    "GRAM-USD",
    "GRT-USD",
    "HBAR-USD",
    "HYPE-USD",
    "IMX-USD",
    "INJ-USD",
    "JTO-USD",
    "LDO-USD",
    "LINK-USD",
    "LIT-USD",
    "LTC-USD",
    "MEGA-USD",
    "MEW-USD",
    "MNT-USD",
    "MON-USD",
    "MOODENG-USD",
    "MORPHO-USD",
    "NEAR-USD",
    "ONDO-USD",
    "OP-USD",
    "ORCA-USD",
    "PAXG-USD",
    "PENGU-USD",
    "PEPE-USD",
    "PNUT-USD",
    "POL-USD",
    "POPCAT-USD",
    "PYTH-USD",
    "QNT-USD",
    "RAY-USD",
    "RENDER-USD",
    "SEI-USD",
    "SHIB-USD",
    "SKY-USD",
    "SNX-USD",
    "SOL-USD",
    "STRK-USD",
    "SUI-USD",
    "SYRUP-USD",
    "TRUMP-USD",
    "UNI-USD",
    "VIRTUAL-USD",
    "VVV-USD",
    "WIF-USD",
    "WLD-USD",
    "WLFI-USD",
    "XCN-USD",
    "XDC-USD",
    "XLM-USD",
    "XPL-USD",
    "XRP-USD",
    "XTZ-USD",
    "ZEC-USD",
    "ZORA-USD",
    "ZRO-USD",
    "ZRX-USD",
)


@dataclass(frozen=True)
class TradingPair:
    symbol: str
    asset_code: str
    quote_code: str = "USD"
    min_order_amount: str | None = None
    is_api_tradable: bool = True
    source: str = "robinhood"


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
        TradingPair(symbol=symbol, asset_code=symbol.split("-")[0], source="robinhood")
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
        asset = str(row.get("asset_code") or symbol.split("-")[0]).upper()
        if asset in _STABLE:
            continue
        if symbol in seen:
            continue
        seen.add(symbol)
        out.append(
            TradingPair(
                symbol=symbol,
                asset_code=asset,
                quote_code=quote,
                min_order_amount=str(row.get("min_order_amount")) if row.get("min_order_amount") else None,
                is_api_tradable=True,
                source="robinhood",
            )
        )
    return out


def resolve_universe(*, robinhood_rows: list[dict[str, Any]] | None = None) -> list[TradingPair]:
    """Robinhood-tradable USD pairs only. Coinbase does not filter this list."""
    if robinhood_rows:
        pairs = pairs_from_robinhood(robinhood_rows)
        if pairs:
            return pairs
    return catalog_pairs()
