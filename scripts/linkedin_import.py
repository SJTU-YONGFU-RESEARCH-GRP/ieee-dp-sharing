#!/usr/bin/env python3
"""
Future LinkedIn API import stub (Workflow D).

Requires approved LinkedIn API access for IEEE-owned organization pages.
Do NOT use for unauthorized member comment scraping.

Environment variables (when enabled):
  LINKEDIN_ACCESS_TOKEN  - OAuth token with r_organization_social / w_organization_social
  LINKEDIN_ORG_URN       - e.g. urn:li:organization:12345

Usage (not active until credentials are configured):
  python3 scripts/linkedin_import.py --dry-run
  python3 scripts/linkedin_import.py --output data/linkedin-staging.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGING_PATH = ROOT / "data" / "linkedin-staging.json"

# Posts API reference:
# https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api


def build_staging_entry(post: dict) -> dict:
    """Map a LinkedIn API post object to our entry schema (pending moderation)."""
    text = post.get("commentary", post.get("text", "")).strip()
    post_id = post.get("id", "unknown")
    slug_base = text[:40] if text else post_id
    entry_id = f"linkedin-{slug_base.lower().replace(' ', '-')[:40]}"

    return {
        "id": entry_id,
        "text": text,
        "display_name": "IEEE DataPort",
        "affiliation": "IEEE",
        "profile_url": None,
        "source_type": "linkedin_post",
        "source_url": post.get("permalink", post.get("url")),
        "event": None,
        "society": None,
        "region": "Global",
        "dataset_topic": None,
        "post_type": "announcement",
        "consent_status": "pending",
        "consent_note": "Imported from IEEE-owned LinkedIn page; requires editorial review.",
        "moderation_status": "pending",
        "approved_by": None,
        "approved_at": None,
        "submitted_at": date.today().isoformat(),
        "published_at": None,
        "featured": False,
        "tags": ["linkedin-import"],
        "enrichment": None,
        "_import_meta": {
            "linkedin_post_id": post_id,
            "imported_at": date.today().isoformat(),
        },
    }


def fetch_organization_posts(access_token: str, org_urn: str) -> list[dict]:
    """
    Placeholder for LinkedIn Posts API integration.

    Replace this function once API credentials and product access are approved.
    """
    raise NotImplementedError(
        "LinkedIn API import is not configured. "
        "Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_ORG_URN after API approval, "
        "or continue using manual JSON curation (Workflow A)."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Import IEEE LinkedIn posts (staging only)")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without writing")
    parser.add_argument(
        "--output",
        type=Path,
        default=STAGING_PATH,
        help="Staging JSON path (not merged into entries.json automatically)",
    )
    args = parser.parse_args()

    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    org_urn = os.environ.get("LINKEDIN_ORG_URN")

    if not token or not org_urn:
        print(
            "LinkedIn import skipped: LINKEDIN_ACCESS_TOKEN and LINKEDIN_ORG_URN not set.\n"
            "Manual curation via data/entries.json remains the active workflow.",
            file=sys.stderr,
        )
        return 0

    if args.dry_run:
        print(f"Config OK: org={org_urn}, output={args.output}")
        return 0

    posts = fetch_organization_posts(token, org_urn)
    staging = {
        "source": "linkedin_api",
        "imported_at": date.today().isoformat(),
        "entries": [build_staging_entry(p) for p in posts],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(staging, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(staging['entries'])} staged entries to {args.output}")
    print("Review staging file, then merge approved rows into data/entries.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
