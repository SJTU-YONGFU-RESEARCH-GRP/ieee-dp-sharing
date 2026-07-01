"""Blocklist for removed LinkedIn posts — prevents re-import."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parent.parent
BLOCKLIST_PATH = ROOT / "data" / "blocklist.json"
REMOVAL_LOG_PATH = ROOT / "data" / "removal-log.json"


def normalize_url(url: str | None) -> str | None:
    if not url or not str(url).strip():
        return None
    parsed = urlparse(str(url).strip())
    if not parsed.scheme:
        parsed = urlparse(f"https://{url.strip()}")
    clean = parsed._replace(query="", fragment="")
    path = clean.path.rstrip("/")
    return urlunparse((clean.scheme, clean.netloc, path, "", "", ""))


def load_blocklist() -> dict:
    if not BLOCKLIST_PATH.exists():
        return {"version": "1.0.0", "updated_at": None, "items": []}
    with BLOCKLIST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_blocklist(data: dict) -> None:
    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    BLOCKLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with BLOCKLIST_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def blocklist_index(data: dict) -> tuple[set[str], set[str]]:
    urls: set[str] = set()
    ids: set[str] = set()
    for item in data.get("items", []):
        url = normalize_url(item.get("source_url"))
        if url:
            urls.add(url)
        entry_id = item.get("entry_id")
        if entry_id:
            ids.add(entry_id)
    return urls, ids


def is_blocklisted(
    source_url: str | None,
    entry_id: str | None,
    data: dict | None = None,
) -> tuple[bool, str | None]:
    bl = data if data is not None else load_blocklist()
    urls, ids = blocklist_index(bl)
    url = normalize_url(source_url)
    if entry_id and entry_id in ids:
        return True, "entry_id blocklisted"
    if url and url in urls:
        return True, "url blocklisted"
    return False, None


def blocklist_reason(
    source_url: str | None,
    entry_id: str | None,
    data: dict | None = None,
) -> str | None:
    bl = data if data is not None else load_blocklist()
    for item in bl.get("items", []):
        if entry_id and item.get("entry_id") == entry_id:
            return item.get("reason")
        url = normalize_url(source_url)
        item_url = normalize_url(item.get("source_url"))
        if url and item_url and url == item_url:
            return item.get("reason")
    return None


def add_to_blocklist(
    *,
    entry_id: str | None,
    source_url: str | None,
    reason: str,
    removed_by: str,
    text_preview: str | None = None,
) -> bool:
    data = load_blocklist()
    urls, ids = blocklist_index(data)
    url = normalize_url(source_url)
    if entry_id and entry_id in ids:
        return False
    if url and url in urls:
        return False

    preview = (text_preview or "")[:160]
    item = {
        "entry_id": entry_id,
        "source_url": url,
        "reason": reason,
        "removed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "removed_by": removed_by,
        "text_preview": preview,
    }
    data.setdefault("items", []).append(item)
    save_blocklist(data)
    log_removal(item)
    return True


def log_removal(item: dict) -> None:
    if not REMOVAL_LOG_PATH.exists():
        log = {"version": "1.0.0", "events": []}
    else:
        with REMOVAL_LOG_PATH.open(encoding="utf-8") as f:
            log = json.load(f)
    log.setdefault("events", []).append(item)
    with REMOVAL_LOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
        f.write("\n")
