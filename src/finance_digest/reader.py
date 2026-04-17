"""Read today's snapshot from the questrade-extract SQLite database."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date


@dataclass
class BalanceRow:
    account_number: str
    currency: str
    cash: float
    market_value: float
    total_equity: float
    book_cost: float
    open_pnl: float


@dataclass
class PositionRow:
    account_number: str
    symbol: str
    description: str
    quantity: float
    current_price: float
    average_entry_price: float
    current_market_value: float
    book_cost: float
    open_pnl: float


def load_snapshot(db_path: str, snapshot_date: date | None = None) -> tuple[list[BalanceRow], list[PositionRow]]:
    """Load balances and positions for the given date (defaults to today)."""
    target = (snapshot_date or date.today()).isoformat()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    balances = [
        BalanceRow(**dict(row))
        for row in conn.execute(
            "SELECT account_number, currency, cash, market_value, total_equity, book_cost, open_pnl "
            "FROM questrade_balances WHERE snapshot_date = ?",
            (target,),
        )
    ]

    positions = [
        PositionRow(**dict(row))
        for row in conn.execute(
            "SELECT account_number, symbol, description, quantity, current_price, "
            "average_entry_price, current_market_value, book_cost, open_pnl "
            "FROM questrade_positions WHERE snapshot_date = ?",
            (target,),
        )
    ]

    conn.close()
    return balances, positions
