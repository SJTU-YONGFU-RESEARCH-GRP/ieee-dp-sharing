# Data directory

## Published content

| File | Purpose |
|------|---------|
| `entries.json` | **Live dataset** — only approved entries appear on the site |
| `schema.json` | JSON schema for each entry |

## LinkedIn `#ieeedataport` intake (editorial)

| File | Purpose |
|------|---------|
| `linkedin-staging.csv` | Daily manual discovery — one row per LinkedIn post |
| `linkedin-staging.json` | Optional API staging (gitignored if generated locally) |

### CSV columns

| Column | Required | Description |
|--------|----------|-------------|
| `status` | | Leave empty or `new` to import. Set `skip` to ignore. Script sets `merged` after import. |
| `found_date` | yes | `YYYY-MM-DD` when the post was found |
| `hashtag` | | e.g. `ieeedataport` |
| `post_url` | yes | Public LinkedIn post URL |
| `profile_url` | | Author profile URL if shown |
| `display_name` | yes | Name as shown on LinkedIn |
| `affiliation` | | University / company |
| `text` | yes | Post or comment text to republish |
| `post_type` | | `testimonial`, `discussion`, `feedback`, etc. |
| `event` | | Related IEEE event |
| `society` | | IEEE society |
| `region` | | `North America`, `Europe`, … |
| `dataset_topic` | | Dataset subject area |
| `tags` | | Comma-separated tags |
| `consent_observed` | | `public_hashtag`, `dm_confirmed`, `author_submitted`, `unknown` |
| `editor_notes` | | Internal notes (not shown on site) |
| `entry_id` | | Filled by `merge_staging.py` after merge |

### Daily editor workflow

1. Search LinkedIn for `#ieeedataport`
2. Add rows to `linkedin-staging.csv`
3. Push to `main` (or wait for daily pipeline)
4. `merge_staging.py` creates **pending** entries in `entries.json`
5. After consent check: `python3 scripts/approve_entry.py <id> --by <editor>`
6. Site rebuilds via GitHub Actions

See [`docs/EDITORIAL_WORKFLOW.md`](../docs/EDITORIAL_WORKFLOW.md).
