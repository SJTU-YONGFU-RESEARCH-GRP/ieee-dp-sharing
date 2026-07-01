"""Detect demo/placeholder source URLs that must not appear as public links."""

from __future__ import annotations

from typing import Optional

PLACEHOLDER_URL_PATTERNS = (
    "seed-sample",
    "seed_sample",
    "example-dataport",
    "/posts/test-",
    "placeholder",
)


def is_placeholder_source_url(url: Optional[str]) -> bool:
    if not url:
        return False
    lower = url.lower()
    return any(p in lower for p in PLACEHOLDER_URL_PATTERNS)


def sanitize_entry_source(entry: dict) -> bool:
    """Null placeholder source_url; return True if entry was modified."""
    url = entry.get("source_url")
    note = (entry.get("consent_note") or "").lower()
    if not is_placeholder_source_url(url) and "seed sample" not in note:
        return False
    entry["source_url"] = None
    entry["source_type"] = "manual_submission"
    return True
