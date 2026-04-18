"""Push digest to a self-hosted ntfy instance."""

from __future__ import annotations

import logging
from datetime import date

import requests

logger = logging.getLogger(__name__)


def push(ntfy_url: str, summary: str, snapshot_date: date) -> None:
    """POST the digest to ntfy. ntfy_url is the full topic URL."""
    title = f"Portfolio Digest — {snapshot_date.isoformat()}"

    try:
        resp = requests.post(
            ntfy_url,
            json={
                "message": summary,
                "title": title,
                "priority": "default",
                "tags": ["chart_increasing"],
                "markdown": True,
            },
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("Digest pushed to ntfy (%s)", ntfy_url)
    except requests.RequestException:
        logger.exception("Failed to push digest to ntfy")
        raise
