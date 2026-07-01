#!/usr/bin/env python3
"""Add lightweight sentiment/topic enrichment to approved entries."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_PATH = ROOT / "data" / "entries.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_analysis import detect_sentiment, detect_topics, extract_quote  # noqa: E402


def enrich_entry(entry: dict) -> dict | None:
    if entry.get("moderation_status") != "approved":
        return None
    if entry.get("consent_status") != "granted":
        return None

    text = entry.get("text", "")
    tags = entry.get("tags") or []
    sentiment, score = detect_sentiment(text)
    topics = detect_topics(text, tags)

    return {
        "sentiment": sentiment,
        "sentiment_score": round(score, 2),
        "topics": topics,
        "quote": extract_quote(text),
        "enriched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main() -> int:
    with ENTRIES_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for entry in data.get("entries", []):
        enrichment = enrich_entry(entry)
        if enrichment is None:
            continue
        prev = entry.get("enrichment") or {}
        semantic_changed = (
            prev.get("sentiment") != enrichment["sentiment"]
            or prev.get("sentiment_score") != enrichment["sentiment_score"]
            or prev.get("topics") != enrichment["topics"]
            or prev.get("quote") != enrichment["quote"]
        )
        if semantic_changed or not prev:
            entry["enrichment"] = enrichment
            updated += 1

    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with ENTRIES_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Enrichment complete: {updated} entries updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
