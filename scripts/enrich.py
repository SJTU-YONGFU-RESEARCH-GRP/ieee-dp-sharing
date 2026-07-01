#!/usr/bin/env python3
"""Add lightweight sentiment/topic enrichment to approved entries."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_PATH = ROOT / "data" / "entries.json"

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "reproducibility": ["reproducib", "replicate", "repeatable"],
    "citation": ["citation", "cite", "doi", "reference"],
    "metadata": ["metadata", "schema", "descriptor"],
    "open-data": ["open data", "open-data", "open access", "share"],
    "discovery": ["discover", "find", "search", "browse"],
    "usability": ["easy", "straightforward", "workflow", "simple", "clearer"],
    "trust": ["trust", "trusted", "reliable", "credible"],
    "licensing": ["licens", "copyright", "template"],
    "community": ["community", "group", "branch", "member"],
    "review": ["review", "reviewer", "peer"],
}

POSITIVE = [
    "straightforward",
    "easy",
    "appreciated",
    "helped",
    "trusted",
    "much easier",
    "love",
    "great",
    "excellent",
]
NEGATIVE = ["difficult", "confusing", "slow", "frustrat", "problem", "issue", "lack"]
MIXED_MARKERS = ["would love", "but", "however", "wish", "could be"]


def detect_topics(text: str, tags: list[str]) -> list[str]:
    lower = text.lower()
    found = {t for t in tags if t in TOPIC_KEYWORDS}
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            found.add(topic)
    return sorted(found)


def detect_sentiment(text: str) -> tuple[str, float]:
    lower = text.lower()
    pos = sum(1 for w in POSITIVE if w in lower)
    neg = sum(1 for w in NEGATIVE if w in lower)
    mixed = any(m in lower for m in MIXED_MARKERS)

    if mixed and pos > 0:
        return "mixed", 0.35
    if pos > neg and pos > 0:
        score = min(0.95, 0.5 + 0.1 * pos)
        return "positive", score
    if neg > pos:
        score = max(-0.9, -0.3 - 0.1 * neg)
        return "negative", score
    return "neutral", 0.0


def extract_quote(text: str, max_len: int = 220) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if not sentences:
        return text[:max_len]
    best = max(sentences, key=len)
    if len(best) <= max_len:
        return best
    return best[: max_len - 1].rstrip() + "…"


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
