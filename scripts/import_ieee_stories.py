#!/usr/bin/env python3
"""
Import public IEEE DataPort member case studies into data/entries.json.

Reads data/ieee-story-sources.json (curated URLs + quotes from ieee-dataport.org
and transmitter.ieee.org). Optionally fetches pages to fill missing fields.

Usage:
  python3 scripts/import_ieee_stories.py
  python3 scripts/import_ieee_stories.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_PATH = ROOT / "data" / "entries.json"
SOURCES_PATH = ROOT / "data" / "ieee-story-sources.json"

CONSENT_NOTE = (
    "Public member story on ieee-dataport.org or transmitter.ieee.org; "
    "republished with attribution for editorial showcase."
)
EDITOR = "ieee-story-import"
USER_AGENT = "ieee-dp-sharing-editorial-bot/1.0 (+https://github.com/SJTU-YONGFU-RESEARCH-GRP/ieee-dp-sharing)"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_entries(data: dict) -> None:
    data["updated_at"] = date.today().isoformat()
    with ENTRIES_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "member"


def entry_id_for(display_name: str, source_url: str, anchor: Optional[str] = None) -> str:
    key = f"{display_name}|{source_url}|{anchor or ''}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    return f"ieee-{slugify(display_name, 32)}-{digest}"


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/").split("#")[0]


def fetch_page(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def html_to_text(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_quotes(text: str) -> list[str]:
    quotes: list[str] = []
    for pattern in (
        r"[“\"]([^”\"]{25,600})[”\"]",
        r"#####\s*[“\"]([^”\"]+)[”\"]",
    ):
        for match in re.finditer(pattern, text):
            quote = match.group(1).strip()
            if "IEEE DataPort" in quote or "dataport" in quote.lower():
                quotes.append(quote)
    return quotes


def extract_by_line(text: str) -> tuple[Optional[str], Optional[str]]:
    match = re.search(r"By:\s*([^,\n]+?)(?:,\s*([^\n]+))?", text)
    if not match:
        return None, None
    name = match.group(1).strip()
    affiliation = (match.group(2) or "").strip() or None
    return name, affiliation


def extract_benefits_paragraph(text: str) -> Optional[str]:
    match = re.search(
        r"Benefits of (?:Using )?the IEEE DataPort Platform\s+(.{40,500}?)(?:Read testimonial|Newsletter Signup|$)",
        text,
        flags=re.I,
    )
    if match:
        paragraph = match.group(1).strip()
        if len(paragraph) >= 40:
            return paragraph
    return None


def enrich_from_fetch(source: dict[str, Any]) -> dict[str, Any]:
    merged = dict(source)
    url = source["url"]
    try:
        html = fetch_page(url)
    except Exception as exc:
        print(f"  fetch skipped ({exc}): {url}", file=sys.stderr)
        return merged

    text = html_to_text(html)
    if not merged.get("display_name") or not merged.get("text"):
        name, affiliation = extract_by_line(text)
        if name and not merged.get("display_name"):
            merged["display_name"] = name
        if affiliation and not merged.get("affiliation"):
            merged["affiliation"] = affiliation

    if not merged.get("text"):
        quotes = extract_quotes(text)
        if quotes:
            merged["text"] = max(quotes, key=len)
        else:
            benefits = extract_benefits_paragraph(text)
            if benefits:
                merged["text"] = benefits

    return merged


def build_entry(source: dict[str, Any]) -> dict[str, Any]:
    url = normalize_url(source["url"])
    display_name = (source.get("display_name") or "").strip()
    text = (source.get("text") or "").strip()
    if not display_name or not text:
        raise ValueError(f"missing display_name or text for {url}")

    if len(text) < 10:
        raise ValueError(f"text too short for {url}")

    today = date.today().isoformat()
    anchor = source.get("anchor")
    entry_id = entry_id_for(display_name, url, anchor)

    tags = source.get("tags") or ["ieee-dataport", "member-story"]
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.replace(";", ",").split(",") if t.strip()]

    return {
        "id": entry_id,
        "text": text[:5000],
        "display_name": display_name,
        "affiliation": source.get("affiliation"),
        "profile_url": None,
        "source_type": "manual_submission",
        "source_url": url,
        "event": source.get("event"),
        "society": source.get("society"),
        "region": source.get("region"),
        "dataset_topic": source.get("dataset_topic"),
        "post_type": source.get("post_type") or "testimonial",
        "consent_status": "granted",
        "consent_note": CONSENT_NOTE,
        "moderation_status": "approved",
        "approved_by": EDITOR,
        "approved_at": today,
        "submitted_at": source.get("submitted_at") or "2024-01-01",
        "published_at": today,
        "featured": bool(source.get("featured")),
        "tags": sorted(set(tags)),
        "enrichment": None,
    }


def load_entries() -> dict:
    if not ENTRIES_PATH.exists():
        return {"version": "1.0.0", "entries": []}
    return load_json(ENTRIES_PATH)


def merge_entries(existing: list[dict], imported: list[dict]) -> tuple[list[dict], int, int]:
    def key(entry: dict) -> tuple[str, str]:
        return (
            normalize_url(entry.get("source_url") or ""),
            (entry.get("display_name") or "").strip().lower(),
        )

    index: dict[tuple[str, str], int] = {}
    result = list(existing)
    for i, entry in enumerate(result):
        url, name = key(entry)
        if url and name:
            index[(url, name)] = i

    added = updated = 0
    for entry in imported:
        url, name = key(entry)
        lookup = (url, name)
        if url and name and lookup in index:
            prev = result[index[lookup]]
            if prev.get("text") != entry.get("text") or prev.get("id") != entry.get("id"):
                entry["enrichment"] = None
                entry["id"] = prev.get("id", entry["id"])
                result[index[lookup]] = entry
                updated += 1
            continue
        result.append(entry)
        if url and name:
            index[lookup] = len(result) - 1
        added += 1

    return result, added, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Import IEEE DataPort case studies")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing")
    parser.add_argument("--fetch", action="store_true", help="Fetch pages to fill missing fields")
    args = parser.parse_args()

    if not SOURCES_PATH.exists():
        print(f"Missing {SOURCES_PATH}", file=sys.stderr)
        return 1

    catalog = load_json(SOURCES_PATH)
    sources = catalog.get("sources", [])
    imported: list[dict] = []
    errors = 0

    for raw in sources:
        source = dict(raw)
        if args.fetch:
            source = enrich_from_fetch(source)
        try:
            entry = build_entry(source)
            imported.append(entry)
        except ValueError as exc:
            print(f"  skip: {exc}", file=sys.stderr)
            errors += 1

    data = load_entries() if ENTRIES_PATH.exists() else {"version": "1.0.0", "entries": []}
    merged, added, updated = merge_entries(data.get("entries", []), imported)

    if args.dry_run:
        print(f"Dry-run: would import {len(imported)} stories (+{added} new, {updated} updated, {errors} errors)")
        for entry in imported:
            print(f"  - {entry['display_name']}: {entry['text'][:70]}...")
        return 1 if errors else 0

    data["entries"] = merged
    save_entries(data)
    print(
        f"IEEE story import complete: {len(imported)} catalogued, "
        f"+{added} new, {updated} updated, {len(merged)} total ({errors} errors)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
