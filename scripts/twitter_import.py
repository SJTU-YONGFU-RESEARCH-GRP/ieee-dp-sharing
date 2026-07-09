#!/usr/bin/env python3
"""
Twitter / X API import stub for @IEEEDataPort official account posts.

Imports only IEEE-owned account tweets into staging — NOT member hashtag search.
Requires X API v2 credentials (paid Basic tier or higher for user timeline).

Environment variables:
  TWITTER_BEARER_TOKEN   - OAuth 2.0 Bearer token
  TWITTER_USERNAME       - default: IEEEDataPort

Usage (no-op until credentials are set):
  python3 scripts/twitter_import.py --dry-run
  python3 scripts/twitter_import.py --output data/twitter-staging.json

API reference:
  https://developer.x.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
STAGING_PATH = ROOT / "data" / "twitter-staging.json"
DEFAULT_USERNAME = "IEEEDataPort"


def build_staging_entry(tweet: dict[str, Any], *, username: str) -> dict[str, Any]:
    tweet_id = tweet.get("id", "unknown")
    text = (tweet.get("text") or "").strip()
    created = (tweet.get("created_at") or "")[:10] or date.today().isoformat()
    source_url = f"https://twitter.com/{username}/status/{tweet_id}"

    return {
        "id": f"tw-{username.lower()}-{tweet_id}",
        "text": text,
        "display_name": "IEEE DataPort",
        "affiliation": "IEEE",
        "profile_url": f"https://twitter.com/{username}",
        "source_type": "twitter_post",
        "source_url": source_url,
        "event": None,
        "society": None,
        "region": "Global",
        "dataset_topic": None,
        "post_type": "announcement",
        "consent_status": "granted",
        "consent_note": "Imported from IEEE-owned @IEEEDataPort account; editorial showcase.",
        "moderation_status": "approved",
        "approved_by": "twitter-import",
        "approved_at": date.today().isoformat(),
        "submitted_at": created,
        "published_at": created,
        "featured": False,
        "tags": ["twitter-import", "ieeedataport"],
        "enrichment": None,
        "_import_meta": {
            "twitter_tweet_id": tweet_id,
            "twitter_username": username,
            "imported_at": date.today().isoformat(),
        },
    }


def fetch_user_id(bearer_token: str, username: str) -> str:
    """Resolve X user id from username via API v2."""
    import urllib.parse
    import urllib.request

    url = f"https://api.twitter.com/2/users/by/username/{urllib.parse.quote(username)}"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {bearer_token}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    user_id = payload.get("data", {}).get("id")
    if not user_id:
        raise RuntimeError(f"Could not resolve user id for @{username}: {payload}")
    return user_id


def fetch_user_tweets(bearer_token: str, user_id: str, *, max_results: int = 10) -> list[dict]:
    """Fetch recent tweets for a user id."""
    import urllib.parse
    import urllib.request

    params = urllib.parse.urlencode(
        {
            "max_results": min(max(max_results, 5), 100),
            "tweet.fields": "created_at,public_metrics,lang",
            "exclude": "retweets,replies",
        }
    )
    url = f"https://api.twitter.com/2/users/{user_id}/tweets?{params}"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {bearer_token}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("data") or []


def main() -> int:
    parser = argparse.ArgumentParser(description="Import @IEEEDataPort tweets (staging)")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without writing")
    parser.add_argument(
        "--output",
        type=Path,
        default=STAGING_PATH,
        help="Staging JSON path (merged by merge_staging.py)",
    )
    parser.add_argument("--max-results", type=int, default=10, help="Tweets to fetch (5–100)")
    parser.add_argument("--username", default=None, help="X username (default: IEEEDataPort)")
    args = parser.parse_args()

    bearer = os.environ.get("TWITTER_BEARER_TOKEN")
    username = (args.username or os.environ.get("TWITTER_USERNAME") or DEFAULT_USERNAME).lstrip("@")

    if not bearer:
        print(
            "Twitter import skipped: TWITTER_BEARER_TOKEN not set.\n"
            "Set API credentials to import @IEEEDataPort posts into twitter-staging.json.",
            file=sys.stderr,
        )
        return 0

    if args.dry_run:
        print(f"Config OK: username=@{username}, output={args.output}")
        return 0

    user_id = fetch_user_id(bearer, username)
    tweets = fetch_user_tweets(bearer, user_id, max_results=args.max_results)
    staging = {
        "source": "twitter_api",
        "username": username,
        "imported_at": date.today().isoformat(),
        "entries": [build_staging_entry(t, username=username) for t in tweets],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(staging, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(staging['entries'])} staged tweets to {args.output}")
    print("Run: python3 scripts/merge_staging.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
