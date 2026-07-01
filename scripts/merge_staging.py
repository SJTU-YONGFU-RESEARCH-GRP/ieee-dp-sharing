#!/usr/bin/env python3
"""
Merge editorial LinkedIn discoveries into data/entries.json.

Sources (in order):
  1. data/linkedin-staging.csv  — manual #ieeedataport review
  2. data/linkedin-staging.json — optional API / batch staging

By default (AUTO_PUBLISH=true) new rows are approved and published immediately.
Set AUTO_PUBLISH=false or pass --require-approval to keep a manual moderation queue.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_PATH = ROOT / "data" / "entries.json"
CSV_PATH = ROOT / "data" / "linkedin-staging.csv"
JSON_STAGING_PATH = ROOT / "data" / "linkedin-staging.json"

CSV_FIELDNAMES = [
    "status",
    "found_date",
    "hashtag",
    "post_url",
    "profile_url",
    "display_name",
    "affiliation",
    "text",
    "post_type",
    "event",
    "society",
    "region",
    "dataset_topic",
    "tags",
    "consent_observed",
    "editor_notes",
    "entry_id",
]

SKIP_STATUSES = {"skip", "skipped", "merged", "rejected", "ignore"}
IMPORT_STATUSES = {"", "new", "pending", "queue"}

REGION_MAP = {
    "north america": "North America",
    "europe": "Europe",
    "asia-pacific": "Asia-Pacific",
    "latin america": "Latin America",
    "middle east & africa": "Middle East & Africa",
    "global": "Global",
}

POST_TYPES = {
    "testimonial",
    "discussion",
    "announcement",
    "question",
    "feedback",
}

CONSENT_OBSERVED_TO_STATUS = {
    "dm_confirmed": "granted",
    "author_submitted": "granted",
    "public_hashtag": "granted",
    "unknown": "granted",
}

AUTO_PUBLISHER = "auto-pipeline"


def auto_publish_enabled(cli_require_approval: bool) -> bool:
    if cli_require_approval:
        return False
    return os.environ.get("AUTO_PUBLISH", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def apply_auto_publish(entry: dict) -> dict:
    today = date.today().isoformat()
    publish_date = entry.get("submitted_at") or today
    entry["moderation_status"] = "approved"
    entry["consent_status"] = "granted"
    entry["approved_by"] = AUTO_PUBLISHER
    entry["approved_at"] = today
    entry["published_at"] = publish_date
    note = entry.get("consent_note") or ""
    if AUTO_PUBLISHER not in note:
        entry["consent_note"] = (
            f"{note} Auto-published from public #ieeedataport staging.".strip()
        )
    entry["enrichment"] = None
    return entry


def load_entries() -> dict:
    with ENTRIES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_entries(data: dict) -> None:
    data["updated_at"] = date.today().isoformat()
    with ENTRIES_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def normalize_url(url: str | None) -> str | None:
    if not url or not str(url).strip():
        return None
    parsed = urlparse(str(url).strip())
    if not parsed.scheme:
        parsed = urlparse(f"https://{url.strip()}")
    clean = parsed._replace(query="", fragment="")
    path = clean.path.rstrip("/")
    return urlunparse((clean.scheme, clean.netloc, path, "", "", ""))


def slugify(text: str, max_len: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "entry"


def entry_id_for_url(url: str, display_name: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"li-{slugify(display_name, 32)}-{digest}"


def nullable(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_tags(raw: str | None, hashtag: str | None) -> list[str]:
    tags: list[str] = []
    if raw:
        tags.extend(t.strip() for t in raw.split(",") if t.strip())
    if hashtag:
        tag = hashtag.strip().lstrip("#").lower()
        if tag and tag not in tags:
            tags.append(tag)
    return sorted(set(tags))


def consent_from_observed(observed: str | None) -> tuple[str, str | None]:
    key = (observed or "unknown").strip().lower()
    status = CONSENT_OBSERVED_TO_STATUS.get(key, "pending")
    notes = {
        "dm_confirmed": "Author confirmed republication via direct message.",
        "author_submitted": "Author submitted via website form or email.",
        "public_hashtag": "Discovered via public #ieeedataport post.",
        "unknown": "Discovered via editorial staging.",
    }
    return status, notes.get(key, notes["unknown"])


def row_to_entry(row: dict, *, auto_publish: bool) -> dict:
    post_url = normalize_url(row.get("post_url"))
    if not post_url:
        raise ValueError("post_url is required")

    display_name = nullable(row.get("display_name"))
    text = nullable(row.get("text"))
    if not display_name or not text:
        raise ValueError("display_name and text are required")

    found_date = nullable(row.get("found_date")) or date.today().isoformat()
    post_type = nullable(row.get("post_type"))
    if post_type and post_type.lower() not in POST_TYPES:
        post_type = None

    region_raw = nullable(row.get("region"))
    region = REGION_MAP.get(region_raw.lower(), region_raw) if region_raw else None

    consent_status, consent_note = consent_from_observed(row.get("consent_observed"))
    editor_notes = nullable(row.get("editor_notes"))
    if editor_notes:
        consent_note = f"{consent_note} Editor: {editor_notes}"

    entry_id = entry_id_for_url(post_url, display_name)
    hashtag = nullable(row.get("hashtag"))

    entry = {
        "id": entry_id,
        "text": text,
        "display_name": display_name,
        "affiliation": nullable(row.get("affiliation")),
        "profile_url": normalize_url(row.get("profile_url")),
        "source_type": "linkedin_post",
        "source_url": post_url,
        "event": nullable(row.get("event")),
        "society": nullable(row.get("society")),
        "region": region,
        "dataset_topic": nullable(row.get("dataset_topic")),
        "post_type": post_type,
        "consent_status": consent_status,
        "consent_note": consent_note,
        "moderation_status": "pending",
        "approved_by": None,
        "approved_at": None,
        "submitted_at": found_date,
        "published_at": None,
        "featured": False,
        "tags": parse_tags(row.get("tags"), hashtag),
        "enrichment": None,
        "_staging": {
            "hashtag": hashtag or "ieeedataport",
            "consent_observed": nullable(row.get("consent_observed")) or "unknown",
            "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }
    if auto_publish:
        apply_auto_publish(entry)
    return entry


def strip_internal_fields(entry: dict) -> dict:
    return {k: v for k, v in entry.items() if not k.startswith("_")}


def existing_keys(entries: list[dict]) -> tuple[set[str], set[str]]:
    ids: set[str] = set()
    urls: set[str] = set()
    for entry in entries:
        if entry.get("id"):
            ids.add(entry["id"])
        url = normalize_url(entry.get("source_url"))
        if url:
            urls.add(url)
    return ids, urls


def merge_csv_rows(data: dict, *, auto_publish: bool) -> tuple[int, int, int]:
    if not CSV_PATH.exists():
        return 0, 0, 0

    entries: list[dict] = data.setdefault("entries", [])
    ids, urls = existing_keys(entries)

    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return 0, 0, 0
        rows = list(reader)

    added = skipped = errors = 0
    for row in rows:
        status = (row.get("status") or "").strip().lower()
        if status in SKIP_STATUSES:
            skipped += 1
            continue
        if status and status not in IMPORT_STATUSES:
            skipped += 1
            continue

        try:
            entry = row_to_entry(row, auto_publish=auto_publish)
        except ValueError as exc:
            print(f"CSV row skipped ({exc}): {row.get('post_url')}", file=sys.stderr)
            errors += 1
            continue

        url = normalize_url(entry["source_url"])
        if entry["id"] in ids or (url and url in urls):
            row["status"] = "merged"
            row["entry_id"] = entry["id"]
            skipped += 1
            continue

        entries.append(strip_internal_fields(entry))
        ids.add(entry["id"])
        if url:
            urls.add(url)
        row["status"] = "merged"
        row["entry_id"] = entry["id"]
        added += 1

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return added, skipped, errors


def merge_json_staging(data: dict, *, auto_publish: bool) -> tuple[int, int]:
    if not JSON_STAGING_PATH.exists():
        return 0, 0

    with JSON_STAGING_PATH.open(encoding="utf-8") as f:
        staging = json.load(f)

    raw_entries = staging.get("entries", [])
    entries: list[dict] = data.setdefault("entries", [])
    ids, urls = existing_keys(entries)

    added = skipped = 0
    for raw in raw_entries:
        if raw.get("moderation_status") == "rejected":
            skipped += 1
            continue

        try:
            if "source_url" in raw and "display_name" in raw:
                entry = row_to_entry(raw, auto_publish=auto_publish)
            else:
                entry = raw
                entry.setdefault("moderation_status", "pending")
                entry.setdefault("consent_status", "pending")
                if auto_publish:
                    apply_auto_publish(entry)
        except ValueError:
            skipped += 1
            continue

        url = normalize_url(entry.get("source_url"))
        entry_id = entry.get("id")
        if not entry_id:
            if not url:
                skipped += 1
                continue
            entry_id = entry_id_for_url(url, entry.get("display_name", "author"))
            entry["id"] = entry_id

        if entry_id in ids or (url and url in urls):
            skipped += 1
            continue

        entries.append(strip_internal_fields(entry))
        ids.add(entry_id)
        if url:
            urls.add(url)
        added += 1

    return added, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge LinkedIn staging into entries.json")
    parser.add_argument(
        "--require-approval",
        action="store_true",
        help="Keep new entries pending (disables AUTO_PUBLISH for this run)",
    )
    args = parser.parse_args()

    auto_publish = auto_publish_enabled(args.require_approval)
    data = load_entries()
    csv_added, csv_skipped, csv_errors = merge_csv_rows(data, auto_publish=auto_publish)
    json_added, json_skipped = merge_json_staging(data, auto_publish=auto_publish)

    if csv_added or json_added:
        save_entries(data)

    total = len(data.get("entries", []))
    pending = sum(1 for e in data["entries"] if e.get("moderation_status") == "pending")
    published = sum(
        1
        for e in data["entries"]
        if e.get("moderation_status") == "approved" and e.get("published_at")
    )
    mode = "auto-publish" if auto_publish else "require-approval"
    print(
        f"Merge complete ({mode}): +{csv_added} from CSV, +{json_added} from JSON staging "
        f"({csv_skipped + json_skipped} skipped, {csv_errors} CSV errors). "
        f"{total} entries total ({published} published, {pending} pending)."
    )
    return 1 if csv_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
