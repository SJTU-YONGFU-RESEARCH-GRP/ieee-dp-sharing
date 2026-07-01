#!/usr/bin/env python3
"""
Score entries for relevance and tone; optionally remove negative/irrelevant content.

Runs after merge_staging in the daily pipeline. Removed items are blocklisted
so merge_staging will not re-import the same LinkedIn URL.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_PATH = ROOT / "data" / "entries.json"
RULES_PATH = ROOT / "data" / "filter-rules.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blocklist import add_to_blocklist, is_blocklisted  # noqa: E402
from text_analysis import detect_sentiment, relevance_hits  # noqa: E402


def load_rules() -> dict:
    with RULES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_entries() -> dict:
    with ENTRIES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_entries(data: dict) -> None:
    from datetime import date

    data["updated_at"] = date.today().isoformat()
    with ENTRIES_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def evaluate_entry(entry: dict, rules: dict) -> tuple[str | None, str]:
    """Return (decision, reason). decision None means keep."""
    text = (entry.get("text") or "").strip()
    tags = entry.get("tags") or []

    min_len = rules.get("min_text_length", 20)
    max_len = rules.get("max_text_length", 5000)
    if len(text) < min_len:
        return "irrelevant", f"text too short ({len(text)} chars)"
    if len(text) > max_len:
        return "irrelevant", f"text too long ({len(text)} chars)"

    lower = text.lower()
    for pattern in rules.get("spam_patterns", []):
        if pattern.lower() in lower:
            return "spam", f"spam pattern: {pattern}"

    hits = relevance_hits(
        text,
        tags,
        rules.get("relevance_keywords", []),
        rules.get("hashtag_keywords", []),
    )
    min_hits = rules.get("min_relevance_hits", 1)
    if hits < min_hits:
        return "irrelevant", f"low relevance ({hits} keyword hits, need {min_hits})"

    sentiment, score = detect_sentiment(text)
    if rules.get("remove_pure_negative") and sentiment == "negative":
        threshold = rules.get("negative_score_threshold", -0.45)
        if score <= threshold:
            if rules.get("keep_mixed_constructive") and hits >= min_hits + 1:
                return None, "negative but relevant constructive feedback"
            return "negative", f"negative sentiment (score {score})"

    return None, "passed filter"


def prune_entry(entry: dict, reason: str, removed_by: str) -> None:
    add_to_blocklist(
        entry_id=entry.get("id"),
        source_url=entry.get("source_url"),
        reason=reason,
        removed_by=removed_by,
        text_preview=entry.get("text"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter negative/irrelevant entries")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Remove failing entries and add them to blocklist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print decisions without modifying files",
    )
    parser.add_argument(
        "--removed-by",
        default="content-filter",
        help="Actor name recorded in blocklist",
    )
    args = parser.parse_args()

    rules = load_rules()
    data = load_entries()
    entries = data.get("entries", [])

    kept = removed = 0
    surviving: list[dict] = []

    for entry in entries:
        entry_id = entry.get("id")
        url = entry.get("source_url")
        blocked, _ = is_blocklisted(url, entry_id)
        if blocked:
            removed += 1
            if args.apply and not args.dry_run:
                print(f"  drop blocklisted: {entry_id}")
            continue

        decision, reason = evaluate_entry(entry, rules)
        if decision:
            removed += 1
            label = f"{entry_id}: {decision} — {reason}"
            if args.dry_run or not args.apply:
                print(f"  would remove: {label}")
            else:
                print(f"  remove: {label}")
                prune_entry(entry, decision, args.removed_by)
            continue

        kept += 1
        surviving.append(entry)

    if args.apply and not args.dry_run:
        data["entries"] = surviving
        save_entries(data)

    mode = "dry-run" if args.dry_run else ("apply" if args.apply else "report")
    print(f"Filter complete ({mode}): kept {kept}, removed {removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
