"""Shared text analysis for enrich and content filtering."""

from __future__ import annotations

import re

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
NEGATIVE = [
    "terrible",
    "awful",
    "hate",
    "worst",
    "useless",
    "scam",
    "spam",
    "difficult",
    "confusing",
    "slow",
    "frustrat",
    "problem",
    "issue",
    "lack",
]
MIXED_MARKERS = ["would love", "but", "however", "wish", "could be", "needs improvement"]


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

    if mixed and (pos > 0 or neg > 0):
        return "mixed", 0.35
    if pos > neg and pos > 0:
        score = min(0.95, 0.5 + 0.1 * pos)
        return "positive", score
    if neg > pos and neg > 0:
        score = max(-0.9, -0.35 - 0.12 * neg)
        return "negative", score
    return "neutral", 0.0


def relevance_hits(text: str, tags: list[str], keywords: list[str], hashtag_keywords: list[str]) -> int:
    lower = text.lower()
    hits = sum(1 for kw in keywords if kw in lower)
    for tag in tags:
        t = tag.lower().lstrip("#")
        if t in hashtag_keywords or any(kw in t for kw in keywords):
            hits += 1
    for ht in hashtag_keywords:
        if ht in lower:
            hits += 1
    return hits


def extract_quote(text: str, max_len: int = 220) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if not sentences:
        return text[:max_len]
    best = max(sentences, key=len)
    if len(best) <= max_len:
        return best
    return best[: max_len - 1].rstrip() + "…"
