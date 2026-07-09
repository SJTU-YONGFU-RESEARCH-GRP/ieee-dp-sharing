# Member submission funnel

Three ways members can submit reflections; editors merge them into `data/linkedin-staging.csv` and the daily pipeline publishes approved content.

## Option A — Website Submit page (fastest for authors)

1. Author visits **Submit** on the live site (`/submit/`).
2. Fills the form and clicks **Generate CSV row for staging**.
3. Author emails the CSV row to an editor, or opens a PR that appends one line to `data/linkedin-staging.csv`.
4. Editor runs `python3 scripts/merge_staging.py` (or waits for daily pipeline).

Rows use `consent_observed=author_submitted`. LinkedIn post URL is optional; without it the entry is stored as `manual_submission` with no “View source” link.

## Option B — GitHub issue template

1. Author opens [**New member submission issue**](https://github.com/SJTU-YONGFU-RESEARCH-GRP/ieee-dp-sharing/issues/new?template=member-submission.yml).
2. Editor copies fields into `data/linkedin-staging.csv` or batches issues into a CSV for import.

## Option C — Google Form (best for campaigns)

### Recommended form fields

| Form question | Maps to staging field |
|---------------|----------------------|
| Timestamp | `found_date` (auto) |
| Full name | `display_name` |
| Affiliation | `affiliation` |
| Reflection text | `text` |
| LinkedIn post URL | `post_url` |
| Region | `region` |
| IEEE society | `society` |
| Dataset / research topic | `dataset_topic` |
| Tags (optional) | `tags` |

Add a required consent checkbox: *“I consent to IEEE DataPort republishing this reflection with attribution.”*

### Import workflow

1. In Google Forms → **Responses** → **Download CSV (.csv)**.
2. Save to `data/inbox/member-form-export.csv` (create `data/inbox/` if needed).
3. Run:

```bash
python3 scripts/import_form_export.py data/inbox/member-form-export.csv --dry-run
python3 scripts/import_form_export.py data/inbox/member-form-export.csv
python3 scripts/merge_staging.py
git add data/linkedin-staging.csv data/entries.json && git commit -m "content: import member form responses" && git push
```

### Sample export

See [`data/samples/member-form-export-sample.csv`](../data/samples/member-form-export-sample.csv).

### Optional: automate in daily pipeline

Drop the latest Google Form CSV at `data/inbox/member-form-export.csv` before the daily run. The pipeline can import it automatically (see `scripts/daily-pipeline.sh`).

## Editor bookmarklet (LinkedIn discovery)

For posts you find via [#ieeedataport search](https://www.linkedin.com/search/results/all/?keywords=%23ieeedataport%20&origin=GLOBAL_SEARCH_HEADER), use the bookmarklet on the **Editor tools** page (`/editor-tools/`). See [`docs/EDITORIAL_WORKFLOW.md`](EDITORIAL_WORKFLOW.md).

## Consent metadata

| Source | `consent_observed` |
|--------|-------------------|
| Submit page / Google Form / GitHub issue | `author_submitted` |
| Editor bookmarklet from public hashtag post | `public_hashtag` |
| DM confirmation | `dm_confirmed` |

## What we still do not do

- Automated LinkedIn hashtag scraping
- Publishing without consent metadata
- Fake or placeholder “View source” URLs
