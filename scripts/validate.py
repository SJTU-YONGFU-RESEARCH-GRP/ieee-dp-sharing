#!/usr/bin/env python3
"""Validate data/entries.json against data/schema.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_PATH = ROOT / "data" / "entries.json"
SCHEMA_PATH = ROOT / "data" / "schema.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_entry(entry: dict, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"entries[{index}]"

    required = [
        "id",
        "text",
        "display_name",
        "source_type",
        "source_url",
        "consent_status",
        "moderation_status",
        "submitted_at",
    ]
    for field in required:
        if field not in entry:
            errors.append(f"{prefix}: missing required field '{field}'")

    if entry.get("moderation_status") == "approved":
        if entry.get("consent_status") != "granted":
            errors.append(
                f"{prefix}: approved entries must have consent_status='granted'"
            )
        if not entry.get("approved_by"):
            errors.append(f"{prefix}: approved entries require approved_by")
        if not entry.get("approved_at"):
            errors.append(f"{prefix}: approved entries require approved_at")

    if entry.get("consent_status") == "granted" and entry.get("moderation_status") == "approved":
        if not entry.get("published_at"):
            errors.append(
                f"{prefix}: published approved entries should set published_at"
            )

    allowed_source = {
        "linkedin_post",
        "linkedin_comment",
        "twitter_post",
        "facebook_post",
        "manual_submission",
        "event_feedback",
        "email_consented",
    }
    if entry.get("source_type") not in allowed_source:
        errors.append(f"{prefix}: invalid source_type")

    allowed_moderation = {"draft", "pending", "approved", "rejected"}
    if entry.get("moderation_status") not in allowed_moderation:
        errors.append(f"{prefix}: invalid moderation_status")

    return errors


def main() -> int:
    if not ENTRIES_PATH.exists():
        print(f"ERROR: {ENTRIES_PATH} not found", file=sys.stderr)
        return 1

    data = load_json(ENTRIES_PATH)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        print("ERROR: entries must be an array", file=sys.stderr)
        return 1

    ids: set[str] = set()
    all_errors: list[str] = []

    for i, entry in enumerate(entries):
        all_errors.extend(validate_entry(entry, i))
        entry_id = entry.get("id")
        if not entry_id:
            continue
        if entry_id in ids:
            all_errors.append(f"entries[{i}]: duplicate id '{entry_id}'")
        ids.add(entry_id)

    if all_errors:
        print("Validation failed:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    published = sum(
        1
        for e in entries
        if e.get("moderation_status") == "approved"
        and e.get("consent_status") == "granted"
        and e.get("published_at")
    )
    pending = sum(1 for e in entries if e.get("moderation_status") == "pending")

    print(f"OK: {len(entries)} entries ({published} published, {pending} pending)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
