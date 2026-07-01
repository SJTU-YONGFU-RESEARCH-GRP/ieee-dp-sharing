---
name: ieee-dp-content-filter
description: Score, remove, and blocklist negative or irrelevant IEEE DataPort LinkedIn showcase entries. Use when tuning filter-rules.json, debugging score_entries.py, manually pruning posts, or explaining why a #ieeedataport row was blocklisted.
---

# IEEE DataPort content filter

## When to use

- User asks to filter negative/irrelevant LinkedIn posts automatically
- User wants removed posts to stay removed (blocklist)
- Tuning `data/filter-rules.json`
- Debugging why a CSV row was skipped as `blocklisted`

## Pipeline position

```text
merge_staging.py → score_entries.py --apply → enrich.py
```

Daily: `scripts/daily-pipeline.sh` runs all three.

## Key files

| File | Role |
|------|------|
| `data/filter-rules.json` | Relevance keywords, spam patterns, thresholds |
| `data/blocklist.json` | Removed URLs/ids — merge_staging checks this |
| `data/removal-log.json` | Audit trail |
| `scripts/score_entries.py` | Auto decision + removal |
| `scripts/prune_entries.py` | Manual remove + blocklist |
| `scripts/blocklist.py` | Shared blocklist helpers |

## Commands

```bash
python3 scripts/score_entries.py --dry-run    # preview
python3 scripts/score_entries.py --apply      # remove + blocklist
python3 scripts/prune_entries.py --id ID --reason irrelevant --by editor
python3 scripts/prune_entries.py --list
```

## Decision logic (summary)

1. **Spam patterns** in text → remove
2. **Relevance hits** below `min_relevance_hits` → remove as irrelevant
3. **Negative sentiment** below `negative_score_threshold` → remove (unless mixed constructive + relevant)
4. Removed entries → `blocklist.json`; same URL never re-imported

## Docs

Read `docs/CONTENT_FILTER.md` for full tuning guide.
