"""Main digest entry point."""

from __future__ import annotations

import logging
import sys
from datetime import date

from finance_digest import config
from finance_digest.analyst import analyse
from finance_digest.notifier import push
from finance_digest.reader import load_snapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run() -> None:
    logger.info("finance-digest starting")
    today = date.today()

    try:
        anthropic_key = config.anthropic_api_key()
        model = config.ai_model()
        db_path = config.questrade_db_path()
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    ntfy_url = config.ntfy_url()

    balances, positions = load_snapshot(db_path, today)

    if not balances and not positions:
        logger.warning("No data found for %s in %s — has questrade-extract run today?", today, db_path)
        sys.exit(0)

    logger.info("Loaded %d balance rows, %d positions", len(balances), len(positions))

    summary = analyse(balances, positions, today, anthropic_key, model)
    logger.info("Claude analysis complete (%d chars)", len(summary))

    print(summary)

    if ntfy_url:
        push(ntfy_url, summary, today)
    else:
        logger.info("NTFY_URL not set — skipping push (dev mode)")


if __name__ == "__main__":
    run()
