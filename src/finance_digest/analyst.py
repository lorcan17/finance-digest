"""Build the portfolio prompt and call Claude for a prose digest."""

from __future__ import annotations

import logging
from datetime import date

import anthropic

from finance_digest.reader import BalanceRow, PositionRow

logger = logging.getLogger(__name__)

def _portfolio_table(positions: list[PositionRow]) -> str:
    total_mkt = sum(p.current_market_value for p in positions) or 1
    lines = ["| Symbol | Qty | Entry | Current | Mkt Value | Open P&L | % Port |",
             "|--------|-----|-------|---------|-----------|----------|--------|"]
    for p in sorted(positions, key=lambda x: -x.current_market_value):
        lines.append(
            f"| {p.symbol} | {p.quantity:.0f} | {p.average_entry_price:.2f} "
            f"| {p.current_price:.2f} | {p.current_market_value:,.0f} "
            f"| {p.open_pnl:+,.0f} | {p.current_market_value/total_mkt*100:.1f}% |"
        )
    return "\n".join(lines)


def _balance_summary(balances: list[BalanceRow]) -> str:
    # Group by account, show CAD equity (primary view)
    by_account: dict[str, dict[str, BalanceRow]] = {}
    for b in balances:
        by_account.setdefault(b.account_number, {})[b.currency] = b

    lines = ["| Account | Type | Total Equity (CAD) | Cash (CAD) |",
             "|---------|------|--------------------|------------|"]
    for acct, currencies in by_account.items():
        cad = currencies.get("CAD")
        if cad:
            lines.append(f"| {acct} | — | {cad.total_equity:,.2f} | {cad.cash:,.2f} |")
    return "\n".join(lines)


def build_prompt(
    balances: list[BalanceRow],
    positions: list[PositionRow],
    snapshot_date: date,
) -> str:
    total_equity = sum(b.total_equity for b in balances if b.currency == "CAD")
    total_pnl = sum(p.open_pnl for p in positions)

    return f"""You are a personal finance assistant giving a daily portfolio digest to a retail investor.

## Portfolio snapshot — {snapshot_date.isoformat()}

**Total equity (CAD, all accounts):** {total_equity:,.2f}
**Total open P&L across positions:** {total_pnl:+,.2f}

### Account balances
{_balance_summary(balances)}

### Positions
{_portfolio_table(positions)}

---

Write a concise daily digest covering:
1. A 2-3 sentence overall portfolio health summary
2. Notable movers today (day change >±2% or open P&L >±10% of book cost)
3. Any concentration risk worth flagging (single position >20% of portfolio)
4. One brief thing to watch this week

Tone: direct, no fluff. Use markdown. Keep it under 300 words.
This is a push notification so lead with the most important thing."""


def analyse(
    balances: list[BalanceRow],
    positions: list[PositionRow],
    snapshot_date: date,
    api_key: str,
    model: str,
) -> str:
    prompt = build_prompt(balances, positions, snapshot_date)
    client = anthropic.Anthropic(api_key=api_key)

    logger.debug("Calling Claude model=%s", model)
    message = client.messages.create(
        model=model,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
