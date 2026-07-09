"""Shared helpers for linkedin-staging.csv rows."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

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


def csv_escape(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", " ").replace("\n", " ").strip()
    if any(c in text for c in '",\n\r'):
        return '"' + text.replace('"', '""') + '"'
    return text


def row_to_line(row: dict[str, Any]) -> str:
    return ",".join(csv_escape(row.get(field, "")) for field in CSV_FIELDNAMES)


def build_staging_row(
    *,
    post_url: str,
    display_name: str,
    text: str,
    found_date: Optional[str] = None,
    profile_url: Optional[str] = None,
    affiliation: Optional[str] = None,
    post_type: Optional[str] = None,
    event: Optional[str] = None,
    society: Optional[str] = None,
    region: Optional[str] = None,
    dataset_topic: Optional[str] = None,
    tags: Optional[str] = None,
    consent_observed: str = "public_hashtag",
    editor_notes: Optional[str] = None,
    hashtag: str = "ieeedataport",
    status: str = "",
    entry_id: str = "",
) -> dict[str, str]:
    return {
        "status": status,
        "found_date": found_date or date.today().isoformat(),
        "hashtag": hashtag,
        "post_url": post_url,
        "profile_url": profile_url or "",
        "display_name": display_name,
        "affiliation": affiliation or "",
        "text": text,
        "post_type": post_type or "",
        "event": event or "",
        "society": society or "",
        "region": region or "",
        "dataset_topic": dataset_topic or "",
        "tags": tags or "",
        "consent_observed": consent_observed,
        "editor_notes": editor_notes or "",
        "entry_id": entry_id,
    }


def append_rows(csv_path: Path, rows: list[dict[str, str]], *, dry_run: bool = False) -> int:
    if not rows:
        return 0

    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    if dry_run:
        return len(rows)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDNAMES})
    return len(rows)


def parse_form_timestamp(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return date.today().isoformat()
    for fmt in (
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return date.today().isoformat()
