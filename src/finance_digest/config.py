"""Settings — reads env vars and agenix secret files."""

from __future__ import annotations

import os
from pathlib import Path


def _secret(env_var: str, agenix_name: str) -> str | None:
    """Check env var first, then agenix secret file."""
    val = os.environ.get(env_var)
    if val:
        return val
    path = Path(f"/run/agenix/{agenix_name}")
    if path.exists():
        return path.read_text().strip()
    return None


def fmp_api_key() -> str:
    val = _secret("FMP_API_KEY", "fmp-api-key")
    if not val:
        raise RuntimeError("FMP_API_KEY not set — check .env or agenix secret")
    return val


def anthropic_api_key() -> str:
    val = _secret("ANTHROPIC_API_KEY", "anthropic-api-key")
    if not val:
        raise RuntimeError("ANTHROPIC_API_KEY not set — check .env or agenix secret")
    return val


def questrade_db_path() -> str:
    # NixOS extract service writes to STATE_DIRECTORY; dev falls back to local path
    return os.environ.get(
        "QUESTRADE_DB_PATH",
        os.path.expanduser("~/projects/questrade-extract/db/questrade.db"),
    )


def ntfy_url() -> str | None:
    return os.environ.get("NTFY_URL") or None


def ai_model() -> str:
    return os.environ.get("AI_MODEL", "claude-haiku-4-5-20251001")
