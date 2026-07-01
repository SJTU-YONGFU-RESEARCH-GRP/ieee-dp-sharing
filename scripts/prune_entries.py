#!/usr/bin/env python3
"""Manually remove an entry and blocklist it to prevent re-import."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_PATH = ROOT / "data" / "entries.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blocklist import add_to_blocklist, normalize_url  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove entry and blocklist URL/id")
    parser.add_argument("--id", help="Entry id to remove")
    parser.add_argument("--url", help="Blocklist URL without removing by id lookup")
    parser.add_argument("--reason", default="manual", help="Removal reason")
    parser.add_argument("--by", default="editor", help="Who removed it")
    parser.add_argument("--list", action="store_true", help="Show blocklist count")
    args = parser.parse_args()

    if args.list:
        from blocklist import load_blocklist

        bl = load_blocklist()
        print(f"Blocklist: {len(bl.get('items', []))} items")
        for item in bl.get("items", [])[-10:]:
            print(f"  - {item.get('entry_id')} | {item.get('reason')} | {item.get('source_url')}")
        return 0

    if not args.id and not args.url:
        parser.error("Provide --id or --url (or --list)")

    if args.url:
        added = add_to_blocklist(
            entry_id=None,
            source_url=normalize_url(args.url),
            reason=args.reason,
            removed_by=args.by,
        )
        print(f"URL blocklisted: {args.url} ({'new' if added else 'already listed'})")

    if args.id:
        with ENTRIES_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries", [])
        target = next((e for e in entries if e.get("id") == args.id), None)
        if not target:
            print(f"Entry not found: {args.id}", file=sys.stderr)
            return 1

        add_to_blocklist(
            entry_id=target.get("id"),
            source_url=target.get("source_url"),
            reason=args.reason,
            removed_by=args.by,
            text_preview=target.get("text"),
        )
        data["entries"] = [e for e in entries if e.get("id") != args.id]
        data["updated_at"] = date.today().isoformat()
        with ENTRIES_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Removed and blocklisted: {args.id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
