#!/usr/bin/env python3
"""
Facebook Graph API import stub for IEEE DataPort official Page posts.

Imports only IEEE-owned Facebook Page posts into staging — NOT member posts,
groups, or hashtag scraping. Requires a Page access token for a Page you manage.

Environment variables:
  FACEBOOK_PAGE_ACCESS_TOKEN  - Page access token (pages_read_engagement)
  FACEBOOK_PAGE_ID            - Numeric Page ID (preferred)
  FACEBOOK_PAGE_USERNAME      - Optional slug if PAGE_ID unset (e.g. IEEEDataport)

Usage (no-op until credentials are set):
  python3 scripts/facebook_import.py --dry-run
  python3 scripts/facebook_import.py --output data/facebook-staging.json

API reference:
  https://developers.facebook.com/docs/graph-api/reference/page/feed/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
STAGING_PATH = ROOT / "data" / "facebook-staging.json"
GRAPH_VERSION = "v21.0"
DEFAULT_PAGE_NAME = "IEEE DataPort"


def graph_get(path: str, params: dict[str, str]) -> dict[str, Any]:
    query = urlencode(params)
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{path}?{query}"
    request = Request(url, headers={"User-Agent": "ieee-dp-sharing/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def resolve_page_id(token: str, page_id: Optional[str], username: Optional[str]) -> str:
    if page_id:
        return page_id.strip()
    if not username:
        raise RuntimeError("Set FACEBOOK_PAGE_ID or FACEBOOK_PAGE_USERNAME")
    payload = graph_get(username, {"fields": "id,name", "access_token": token})
    resolved = payload.get("id")
    if not resolved:
        raise RuntimeError(f"Could not resolve Facebook page id: {payload}")
    return str(resolved)


def extract_post_text(post: dict[str, Any]) -> str:
    text = (post.get("message") or "").strip()
    if text:
        return text
    attachments = (post.get("attachments") or {}).get("data") or []
    for item in attachments:
        for key in ("title", "description", "name"):
            value = (item.get(key) or "").strip()
            if value:
                return value
        sub = (item.get("subattachments") or {}).get("data") or []
        for child in sub:
            for key in ("title", "description", "name"):
                value = (child.get(key) or "").strip()
                if value:
                    return value
    return ""


def build_staging_entry(
    post: dict[str, Any],
    *,
    page_id: str,
    page_name: str,
    page_username: Optional[str],
) -> Optional[dict[str, Any]]:
    text = extract_post_text(post)
    if len(text) < 10:
        return None

    post_id = str(post.get("id", "unknown"))
    short_id = post_id.split("_")[-1] if "_" in post_id else post_id
    created = (post.get("created_time") or "")[:10] or date.today().isoformat()
    permalink = post.get("permalink_url")
    if not permalink and page_username:
        permalink = f"https://www.facebook.com/{page_username}/posts/{short_id}"
    elif not permalink:
        permalink = f"https://www.facebook.com/{page_id}/posts/{short_id}"

    slug = (page_username or page_id).lower().replace(" ", "-")

    return {
        "id": f"fb-{slug}-{short_id}",
        "text": text[:5000],
        "display_name": page_name,
        "affiliation": "IEEE",
        "profile_url": f"https://www.facebook.com/{page_username or page_id}",
        "source_type": "facebook_post",
        "source_url": permalink,
        "event": None,
        "society": None,
        "region": "Global",
        "dataset_topic": None,
        "post_type": "announcement",
        "consent_status": "granted",
        "consent_note": "Imported from IEEE-owned Facebook Page; editorial showcase.",
        "moderation_status": "approved",
        "approved_by": "facebook-import",
        "approved_at": date.today().isoformat(),
        "submitted_at": created,
        "published_at": created,
        "featured": False,
        "tags": ["facebook-import", "ieeedataport"],
        "enrichment": None,
        "_import_meta": {
            "facebook_post_id": post_id,
            "facebook_page_id": page_id,
            "imported_at": date.today().isoformat(),
        },
    }


def fetch_page_posts(token: str, page_id: str, *, limit: int = 10) -> list[dict[str, Any]]:
    fields = "message,created_time,permalink_url,id,attachments{title,description,subattachments}"
    payload = graph_get(
        f"{page_id}/posts",
        {
            "fields": fields,
            "limit": str(min(max(limit, 1), 50)),
            "access_token": token,
        },
    )
    return payload.get("data") or []


def main() -> int:
    parser = argparse.ArgumentParser(description="Import IEEE DataPort Facebook Page posts")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without writing")
    parser.add_argument(
        "--output",
        type=Path,
        default=STAGING_PATH,
        help="Staging JSON path (merged by merge_staging.py)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Posts to fetch (1–50)")
    parser.add_argument("--page-id", default=None, help="Facebook Page ID override")
    parser.add_argument("--page-username", default=None, help="Facebook Page username/slug")
    args = parser.parse_args()

    token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = args.page_id or os.environ.get("FACEBOOK_PAGE_ID")
    page_username = (args.page_username or os.environ.get("FACEBOOK_PAGE_USERNAME") or "").strip() or None

    if not token:
        print(
            "Facebook import skipped: FACEBOOK_PAGE_ACCESS_TOKEN not set.\n"
            "Set a Page access token to import IEEE DataPort Facebook posts into facebook-staging.json.",
            file=sys.stderr,
        )
        return 0

    if args.dry_run:
        print(
            f"Config OK: page_id={page_id or '(resolve from username)'}, "
            f"username={page_username or '(none)'}, output={args.output}"
        )
        return 0

    resolved_id = resolve_page_id(token, page_id, page_username)
    page_meta = graph_get(resolved_id, {"fields": "name,username", "access_token": token})
    page_name = page_meta.get("name") or DEFAULT_PAGE_NAME
    username = page_meta.get("username") or page_username

    posts = fetch_page_posts(token, resolved_id, limit=args.limit)
    entries = []
    for post in posts:
        entry = build_staging_entry(
            post,
            page_id=resolved_id,
            page_name=page_name,
            page_username=username,
        )
        if entry:
            entries.append(entry)

    staging = {
        "source": "facebook_graph_api",
        "page_id": resolved_id,
        "page_name": page_name,
        "imported_at": date.today().isoformat(),
        "entries": entries,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(staging, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(entries)} staged Facebook posts to {args.output}")
    print("Run: python3 scripts/merge_staging.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
