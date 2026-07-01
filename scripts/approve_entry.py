#!/usr/bin/env python3
"""Approve a pending entry for publication on the showcase site."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_PATH = ROOT / "data" / "entries.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Approve a pending entry for publication")
    parser.add_argument("entry_id", help="Entry id from data/entries.json")
    parser.add_argument("--by", required=True, help="Editor handle or name")
    parser.add_argument(
        "--consent",
        choices=["granted", "pending"],
        default="granted",
        help="Consent status after approval (default: granted)",
    )
    parser.add_argument("--featured", action="store_true", help="Mark as featured")
    parser.add_argument(
        "--reject",
        action="store_true",
        help="Reject instead of approve",
    )
    parser.add_argument(
        "--publish-date",
        help="Published date YYYY-MM-DD (default: today)",
    )
    args = parser.parse_args()

    with ENTRIES_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    target = None
    for entry in data.get("entries", []):
        if entry.get("id") == args.entry_id:
            target = entry
            break

    if target is None:
        print(f"Entry not found: {args.entry_id}", file=sys.stderr)
        return 1

    today = date.today().isoformat()
    publish_date = args.publish_date or today

    if args.reject:
        target["moderation_status"] = "rejected"
        target["approved_by"] = args.by
        target["approved_at"] = today
        target["published_at"] = None
        print(f"Rejected: {args.entry_id}")
    else:
        if args.consent != "granted":
            print(
                "Warning: approving with consent=pending — entry will not appear publicly "
                "until consent_status is granted and published_at is set.",
                file=sys.stderr,
            )
        target["moderation_status"] = "approved"
        target["consent_status"] = args.consent
        target["approved_by"] = args.by
        target["approved_at"] = today
        target["published_at"] = publish_date if args.consent == "granted" else None
        target["featured"] = bool(args.featured)
        print(f"Approved: {args.entry_id} (published_at={target['published_at']})")

    data["updated_at"] = today
    with ENTRIES_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("Run: python3 scripts/enrich.py && npm run validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
