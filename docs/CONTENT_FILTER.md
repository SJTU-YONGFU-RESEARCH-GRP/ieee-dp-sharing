# Content filtering and blocklist

Automatic removal of **irrelevant**, **spam**, or **strongly negative** posts, with a **blocklist** so removed LinkedIn URLs are never re-imported.

## Pipeline order

```text
merge_staging.py   → import CSV rows
score_entries.py   → filter + blocklist bad entries
enrich.py          → tag surviving entries
deploy
```

## What gets removed automatically

Configured in [`data/filter-rules.json`](../data/filter-rules.json):

| Rule | Example |
|------|---------|
| **Irrelevant** | No IEEE/DataPort/dataset keywords |
| **Spam** | "click here", crypto pitches, etc. |
| **Negative** | Strongly negative tone without constructive relevance |
| **Too short** | Under 20 characters |

**Kept:** constructive mixed feedback (e.g. "love DataPort but wish licensing was clearer") when relevance keywords match.

## Blocklist (no re-import)

Removed posts are recorded in [`data/blocklist.json`](../data/blocklist.json).

If the same `post_url` appears again in `linkedin-staging.csv`, `merge_staging.py` skips it and marks the CSV row `status=blocklisted`.

Audit trail: [`data/removal-log.json`](../data/removal-log.json)

## Commands

```bash
# Preview what would be removed
npm run filter:dry

# Apply filter (also runs in daily pipeline)
npm run filter

# Manually remove + blocklist
python3 scripts/prune_entries.py --id li-jane-doe-abc123 --reason irrelevant --by editor
python3 scripts/prune_entries.py --url "https://www.linkedin.com/posts/..." --reason spam

# View blocklist
python3 scripts/prune_entries.py --list
```

## Tuning rules

Edit `data/filter-rules.json`:

- `min_relevance_hits` — raise to be stricter
- `relevance_keywords` — add domain terms
- `spam_patterns` — add spam phrases
- `negative_score_threshold` — lower = remove more negative posts
- `keep_mixed_constructive: true` — keep useful criticism

## Daily automation

`scripts/daily-pipeline.sh` runs:

```bash
python3 scripts/score_entries.py --apply
```

after merge, before enrich.
