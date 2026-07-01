#!/usr/bin/env python3
"""Write data/pipeline-status.json for the site status panel."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_PATH = ROOT / "data" / "entries.json"
BLOCKLIST_PATH = ROOT / "data" / "blocklist.json"
CSV_PATH = ROOT / "data" / "linkedin-staging.csv"
STAMP_PATH = ROOT / "data" / ".deploy-stamp"
OUT_PATH = ROOT / "data" / "pipeline-status.json"


def count_csv_queue() -> int:
    if not CSV_PATH.exists():
        return 0
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return sum(
        1
        for r in rows
        if (r.get("status") or "").strip().lower() in {"", "new", "pending", "queue"}
        and (r.get("post_url") or "").strip()
    )


def main() -> int:
    entries = json.loads(ENTRIES_PATH.read_text(encoding="utf-8"))
    all_entries = entries.get("entries", [])
    published = sum(
        1
        for e in all_entries
        if e.get("moderation_status") == "approved"
        and e.get("consent_status") == "granted"
        and e.get("published_at")
    )
    pending = sum(1 for e in all_entries if e.get("moderation_status") == "pending")

    blocklist_count = 0
    if BLOCKLIST_PATH.exists():
        blocklist_count = len(json.loads(BLOCKLIST_PATH.read_text(encoding="utf-8")).get("items", []))

    last_run = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if STAMP_PATH.exists():
        stamp = STAMP_PATH.read_text(encoding="utf-8").strip()
        if stamp:
            last_run = stamp

    status = {
        "last_pipeline_run": last_run,
        "data_updated_at": entries.get("updated_at"),
        "auto_publish": True,
        "content_filter_enabled": True,
        "published_count": published,
        "pending_count": pending,
        "total_entries": len(all_entries),
        "blocklist_count": blocklist_count,
        "staging_queue_rows": count_csv_queue(),
    }

    OUT_PATH.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(f"Pipeline status written: {published} published, {blocklist_count} blocklisted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
