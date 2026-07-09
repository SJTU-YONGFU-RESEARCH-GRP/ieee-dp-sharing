# Editorial workflow: `#ieeedataport` LinkedIn intake

Compliant collection model — **no automated LinkedIn scraping**. Editors discover posts manually, stage them in CSV, and approve before publication.

## Overview

```text
Daily: search LinkedIn for #ieeedataport
        ↓
Add row to data/linkedin-staging.csv
        ↓
merge_staging.py (AUTO_PUBLISH=true) → approved + published_at set
        ↓
enrich.py → git push → site deploy
```

Optional manual gate: set `AUTO_PUBLISH=false` or run `merge_staging.py --require-approval`, then use `approve_entry.py`.

Public site: [ieee-dp-sharing](https://sjtu-yongfu-research-grp.github.io/ieee-dp-sharing/)  
Moderation queue: `/moderation/`

## Step 1 — Discover posts on LinkedIn

1. Log in to LinkedIn (normal browser).
2. Open [#ieeedataport search on LinkedIn](https://www.linkedin.com/search/results/all/?keywords=%23ieeedataport%20&origin=GLOBAL_SEARCH_HEADER).
3. For each relevant **public** post, either:
   - **Bookmarklet (fast):** install **IEEE DP Capture** from the site’s [Editor tools](/editor-tools/) page, open the post, click the bookmarklet → CSV row copied → paste into `linkedin-staging.csv`
   - **Manual:** copy post URL, author, text, affiliation

Do **not** collect private messages, emails, or profile data beyond what is needed for attribution.

## Step 1b — Member submissions (no LinkedIn required)

Members can submit via the [Submit](/submit/) page, [GitHub issue template](https://github.com/SJTU-YONGFU-RESEARCH-GRP/ieee-dp-sharing/issues/new?template=member-submission.yml), or Google Form.

See [`docs/MEMBER_SUBMISSION.md`](MEMBER_SUBMISSION.md) for Google Form import:

```bash
python3 scripts/import_form_export.py data/inbox/member-form-export.csv
```

## Step 2 — Add a CSV row

Edit [`data/linkedin-staging.csv`](../data/linkedin-staging.csv):

```csv
status,found_date,hashtag,post_url,profile_url,display_name,affiliation,text,post_type,event,society,region,dataset_topic,tags,consent_observed,editor_notes,entry_id
new,2026-07-01,ieeedataport,https://www.linkedin.com/posts/activity-123...,https://www.linkedin.com/in/example/,Alex Rivera,MIT,We just published our smart-grid dataset on @IEEE DataPort — the DOI made citation easy for our IEEE conference paper.,testimonial,,IEEE Power & Energy Society,North America,Smart Grid,open-data;citation,public_hashtag,Strong testimonial; verify DM consent before approve,
```

| `consent_observed` | Meaning |
|--------------------|---------|
| `public_hashtag` | Found via hashtag; confirm republication is OK |
| `dm_confirmed` | Author agreed in LinkedIn DM or email |
| `author_submitted` | Author used the Submit page |
| `unknown` | Not yet contacted |

Leave `status` empty or `new`. Leave `entry_id` empty (filled by merge script).

## Step 3 — Merge (auto-publish by default)

```bash
python3 scripts/merge_staging.py
```

Or push to `main` and let **Daily pipeline** run it. New rows are **approved and published immediately** unless you set:

```bash
AUTO_PUBLISH=false python3 scripts/merge_staging.py --require-approval
```

## Step 4 — Optional manual approve

Only needed when `AUTO_PUBLISH=false`:

```bash
python3 scripts/approve_entry.py li-alex-rivera-abc1234567 --by your-github-handle
python3 scripts/enrich.py
python3 scripts/validate.py
git add data/ && git commit -m "content: approve Alex Rivera testimonial" && git push
```

Options:

```bash
# Featured on homepage
python3 scripts/approve_entry.py <id> --by editor --featured

# Reject
python3 scripts/approve_entry.py <id> --by editor --reject
```

## Step 5 — Site updates

Push to `main` triggers:

1. **Daily pipeline** (scheduled) — merge → enrich → validate → commit → push
2. **Deploy to GitHub Pages** — rebuild from `gh-pages` branch

## Member self-submission

Authors can use the [**Submit**](../src/pages/submit.astro) page to generate JSON for a pull request. Encourage posts that use `#ieeedataport` to also submit their URL for faster approval.

## What we do not do

- Scrape LinkedIn with bots or browser automation
- Auto-publish without `moderation_status: approved`
- Display entries without appropriate consent metadata

## Optional: IEEE org LinkedIn API

When API access is approved, `scripts/linkedin_import.py` can stage **IEEE-owned page** posts to `data/linkedin-staging.json`. Run `merge_staging.py` to import those into the same queue. This does **not** replace hashtag editorial review for member posts.

## Commands cheat sheet

| Command | Purpose |
|---------|---------|
| `python3 scripts/merge_staging.py` | Import CSV (+ JSON staging) → `entries.json` |
| `python3 scripts/import_ieee_stories.py` | Import ieee-dataport.org case studies |
| `python3 scripts/twitter_import.py` | Import @IEEEDataPort tweets (needs API token) |
| `python3 scripts/facebook_import.py` | Import IEEE DataPort Facebook Page (needs Page token) |
| `python3 scripts/build_bookmarklet.py` | Rebuild editor bookmarklet (`prebuild` runs automatically) |
| `python3 scripts/approve_entry.py <id> --by <editor>` | Approve for publication |
| `python3 scripts/enrich.py` | Sentiment/topics on approved entries |
| `python3 scripts/validate.py` | Schema check |
| `./scripts/daily-pipeline.sh` | Full local pipeline |
| `./scripts/build-and-push.sh --force-deploy` | Push + trigger deploy |
