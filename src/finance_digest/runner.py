"""Main digest entry point."""

from __future__ import annotations

import logging
import sys
import time
from datetime import date

from finance_digest import config
from finance_digest.analyst import analyse
from finance_digest.notifier import push
from finance_digest.reader import load_snapshot
from finance_digest.telemetry import setup_meter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run() -> None:
    provider, meter = setup_meter("finance-digest")
    run_duration = meter.create_histogram("finance_digest.run.duration_seconds", unit="s")
    run_status = meter.create_gauge("finance_digest.run.exit_status")
    input_tokens = meter.create_counter("finance_digest.claude.input_tokens")
    output_tokens = meter.create_counter("finance_digest.claude.output_tokens")
    ntfy_delivered = meter.create_gauge("finance_digest.ntfy.delivered")

    t0 = time.perf_counter()
    status = 0
    try:
        logger.info("finance-digest starting")
        today = date.today()

        try:
            anthropic_key = config.anthropic_api_key()
            model = config.ai_model()
            db_path = config.questrade_db_path()
        except RuntimeError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            status = 1
            sys.exit(1)
        ntfy_url = config.ntfy_url()

        balances, positions = load_snapshot(db_path, today)

        if not balances and not positions:
            logger.warning("No data found for %s in %s — has questrade-extract run today?", today, db_path)
            sys.exit(0)

        logger.info("Loaded %d balance rows, %d positions", len(balances), len(positions))

        summary, usage = analyse(balances, positions, today, anthropic_key, model)
        input_tokens.add(usage.input_tokens, {"model": model})
        output_tokens.add(usage.output_tokens, {"model": model})
        logger.info("Claude analysis complete (%d chars)", len(summary))

        print(summary)

        if ntfy_url:
            try:
                push(ntfy_url, summary, today)
                ntfy_delivered.set(1)
            except Exception:
                ntfy_delivered.set(0)
                raise
        else:
            logger.info("NTFY_URL not set — skipping push (dev mode)")

    except Exception:
        status = 1
        raise
    finally:
        run_duration.record(time.perf_counter() - t0)
        run_status.set(status)
        try:
            provider.shutdown()
        except Exception:
            logger.warning("OTel shutdown failed", exc_info=True)


if __name__ == "__main__":
    run()
