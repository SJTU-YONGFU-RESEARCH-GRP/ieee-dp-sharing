#!/usr/bin/env python3
"""
Import Google Form (or similar) CSV exports into data/linkedin-staging.csv.

Members submit via Google Form → editor downloads CSV → this script appends staging rows.

Usage:
  python3 scripts/import_form_export.py path/to/form-responses.csv
  python3 scripts/import_form_export.py data/inbox/member-form-export.csv --dry-run
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "data" / "linkedin-staging.csv"
INBOX_DIR = ROOT / "data" / "inbox"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from staging_csv import append_rows, build_staging_row, parse_form_timestamp  # noqa: E402

# Fuzzy match: normalized header -> staging field
HEADER_ALIASES: dict[str, list[str]] = {
    "found_date": ["timestamp", "submission time", "date", "submitted at"],
    "display_name": ["full name", "name", "your name", "display name"],
    "affiliation": ["affiliation", "organization", "university", "institution", "employer"],
    "text": [
        "reflection",
        "reflection text",
        "testimonial",
        "your reflection",
        "what would you like to share",
        "message",
    ],
    "post_url": [
        "linkedin post url",
        "post url",
        "linkedin url",
        "source url",
        "public source url",
        "link to your linkedin post",
    ],
    "profile_url": ["linkedin profile", "profile url", "linkedin profile url"],
    "post_type": ["post type", "type"],
    "event": ["event", "conference", "ieee event"],
    "society": ["ieee society", "society"],
    "region": ["region"],
    "dataset_topic": ["dataset topic", "topic", "research topic"],
    "tags": ["tags", "keywords"],
    "editor_notes": ["additional notes", "notes", "comments", "anything else"],
}


def normalize_header(header: str) -> str:
    text = header.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def map_headers(headers: list[str]) -> dict[str, str]:
    """Map export column names to staging fields."""
    mapping: dict[str, str] = {}
    normalized = {normalize_header(h): h for h in headers}

    for field, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            key = normalize_header(alias)
            if key in normalized:
                mapping[field] = normalized[key]
                break

    return mapping


def row_from_export(raw: dict[str, str], column_map: dict[str, str]) -> dict[str, str] | None:
    def get(field: str) -> str:
        col = column_map.get(field)
        if not col:
            return ""
        return (raw.get(col) or "").strip()

    display_name = get("display_name")
    text = get("text")
    post_url = get("post_url")

    if not display_name or not text:
        return None

    found_raw = get("found_date")
    tags = get("tags")
    if "ieeedataport" not in tags.lower() and "#ieeedataport" in text.lower():
        tags = f"ieeedataport;{tags}" if tags else "ieeedataport"

    notes = get("editor_notes")
    if notes:
        notes = f"Google Form import. {notes}"
    else:
        notes = "Google Form import."

    if not post_url:
        notes = f"{notes} No LinkedIn post URL provided."

    return build_staging_row(
        post_url=post_url,
        display_name=display_name,
        text=text,
        found_date=parse_form_timestamp(found_raw) if found_raw else None,
        profile_url=get("profile_url") or None,
        affiliation=get("affiliation") or None,
        post_type=get("post_type") or "testimonial",
        event=get("event") or None,
        society=get("society") or None,
        region=get("region") or None,
        dataset_topic=get("dataset_topic") or None,
        tags=tags or "ieeedataport",
        consent_observed="author_submitted",
        editor_notes=notes,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Google Form CSV into linkedin-staging.csv")
    parser.add_argument("export_csv", type=Path, help="Downloaded form responses CSV")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CSV,
        help="Staging CSV to append (default: data/linkedin-staging.csv)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print rows without writing")
    args = parser.parse_args()

    if not args.export_csv.exists():
        print(f"File not found: {args.export_csv}", file=sys.stderr)
        return 1

    with args.export_csv.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            print("CSV has no header row.", file=sys.stderr)
            return 1
        column_map = map_headers(list(reader.fieldnames))
        if "display_name" not in column_map or "text" not in column_map:
            print(
                "Could not map required columns (name + reflection text). "
                f"Headers: {reader.fieldnames}",
                file=sys.stderr,
            )
            return 1

        rows: list[dict[str, str]] = []
        skipped = 0
        for raw in reader:
            row = row_from_export(raw, column_map)
            if row is None:
                skipped += 1
                continue
            rows.append(row)

    if args.dry_run:
        for row in rows:
            print(f"  + {row['display_name']}: {row['text'][:60]}...")
        print(f"Dry-run: would append {len(rows)} row(s), skipped {skipped}")
        return 0

    added = append_rows(args.output, rows)
    print(f"Imported {added} row(s) into {args.output} (skipped {skipped})")
    print("Next: python3 scripts/merge_staging.py && git add data/ && git push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
