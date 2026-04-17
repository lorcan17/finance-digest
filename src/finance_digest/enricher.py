"""Fetch current quotes from FMP for each unique symbol in the portfolio."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

_BASE = "https://financialmodelingprep.com/stable"


@dataclass
class Quote:
    symbol: str
    price: float
    change_pct: float
    market_cap: float | None
    pe_ratio: float | None
    year_high: float | None
    year_low: float | None


def fetch_quotes(symbols: list[str], api_key: str) -> dict[str, Quote]:
    """Return a dict of symbol → Quote. Missing symbols are silently skipped."""
    if not symbols:
        return {}

    results: dict[str, Quote] = {}
    batch = ",".join(symbols)

    try:
        resp = requests.get(
            f"{_BASE}/quote",
            params={"symbol": batch, "apikey": api_key},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.exception("FMP quote fetch failed for %s", batch)
        return results

    for item in data if isinstance(data, list) else []:
        sym = item.get("symbol", "")
        if not sym:
            continue
        results[sym] = Quote(
            symbol=sym,
            price=item.get("price", 0.0),
            change_pct=item.get("changePercentage", 0.0),
            market_cap=item.get("marketCap"),
            pe_ratio=item.get("pe"),
            year_high=item.get("yearHigh"),
            year_low=item.get("yearLow"),
        )
        logger.debug("FMP %s: price=%.2f change=%.2f%%", sym, results[sym].price, results[sym].change_pct)

    missing = set(symbols) - set(results)
    if missing:
        logger.warning("FMP returned no data for: %s", ", ".join(sorted(missing)))

    return results
