# IEEE DataPort Member Voices

A static showcase website for curated IEEE DataPort member reflections, testimonials, and feedback — hosted on **GitHub Pages** with consent-based moderation and lightweight semantic insights.

> **Positioning:** A curated member-engagement showcase, not a LinkedIn scraper.

## Live workflow

### LinkedIn `#ieeedataport` intake (active)

1. Editors search LinkedIn for **`#ieeedataport`** and add rows to [`data/linkedin-staging.csv`](data/linkedin-staging.csv)
2. `python3 scripts/merge_staging.py` auto-publishes new rows (`AUTO_PUBLISH=true` by default)
3. Daily pipeline: merge → **filter** → enrich → push → site deploy

Negative/irrelevant posts are removed automatically; removed URLs are **blocklisted** so they are not re-imported. See [`docs/CONTENT_FILTER.md`](docs/CONTENT_FILTER.md).

To require manual approval: `AUTO_PUBLISH=false python3 scripts/merge_staging.py --require-approval`

Full guide: [`docs/EDITORIAL_WORKFLOW.md`](docs/EDITORIAL_WORKFLOW.md)

### Member submit + form import

1. [**Submit**](src/pages/submit.astro) page → **CSV row** for `linkedin-staging.csv` (recommended), JSON, or [GitHub issue](.github/ISSUE_TEMPLATE/member-submission.yml)
2. Google Form → download CSV → `python3 scripts/import_form_export.py data/inbox/member-form-export.csv`
3. Guide: [`docs/MEMBER_SUBMISSION.md`](docs/MEMBER_SUBMISSION.md)

### Editor bookmarklet (LinkedIn discovery)

1. Open **Editor tools** (`/editor-tools/`) on the live site
2. Drag **IEEE DP Capture** to bookmarks bar
3. On a LinkedIn post → click bookmarklet → paste CSV row into `data/linkedin-staging.csv`

Full guide: [`docs/EDITORIAL_WORKFLOW.md`](docs/EDITORIAL_WORKFLOW.md)

### IEEE case studies (automated)

`python3 scripts/import_ieee_stories.py` imports public member quotes from [`data/ieee-story-sources.json`](data/ieee-story-sources.json) (ieee-dataport.org + transmitter.ieee.org). Runs in the daily pipeline before merge.

### Twitter / X (`@IEEEDataPort`, optional)

1. Add repository secret `TWITTER_BEARER_TOKEN` (X API v2)
2. Optional: `TWITTER_USERNAME` (default `IEEEDataPort`)
3. `python3 scripts/twitter_import.py` → `data/twitter-staging.json` → `merge_staging.py`

Official account posts only — not member hashtag search.

### Facebook Page (optional)

1. Create a [Meta for Developers](https://developers.facebook.com/) app with **pages_read_engagement**
2. Generate a **Page access token** for the IEEE DataPort Facebook Page you manage
3. Add repository secrets:
   - `FACEBOOK_PAGE_ACCESS_TOKEN`
   - `FACEBOOK_PAGE_ID` (numeric) or `FACEBOOK_PAGE_USERNAME`
4. `python3 scripts/facebook_import.py` → `data/facebook-staging.json` → `merge_staging.py`

Official Page posts only — not member profiles, groups, or public scraping.

### LinkedIn API (future, IEEE org pages only)

1. Add repository secrets:
   - `LINKEDIN_ACCESS_TOKEN`
   - `LINKEDIN_ORG_URN` (e.g. `urn:li:organization:12345`)
2. Implement `fetch_organization_posts()` in [`scripts/linkedin_import.py`](scripts/linkedin_import.py)
3. Daily workflow stages imports to `data/linkedin-staging.json`
4. Editors review and merge approved rows into `data/entries.json`

**Do not** use unauthorized scraping, browser automation, or member comment harvesting.

## Pages

| Page | Path | Description |
|------|------|-------------|
| Showcase | `/` | Filterable testimonial cards |
| Insights | `/insights/` | Topic and sentiment summaries |
| Moderation | `/moderation/` | Pending queue for editors |
| Editor tools | `/editor-tools/` | LinkedIn capture bookmarklet + import docs |
| Submit | `/submit/` | CSV/JSON generator + member funnel |

## Data schema

Each entry in `data/entries.json` follows [`data/schema.json`](data/schema.json).

Required moderation fields:

- `consent_status`: `pending` \| `granted` \| `revoked`
- `moderation_status`: `draft` \| `pending` \| `approved` \| `rejected`
- `approved_by`, `approved_at`, `published_at` (for published content)

Only entries with `moderation_status: "approved"`, `consent_status: "granted"`, and a `published_at` date appear on the public site.

## Local development

```bash
npm install
npm run dev
npm run merge      # import linkedin-staging.csv → entries.json
npm run validate
npm run enrich
```

For local preview matching GitHub Pages subpath:

```bash
BASE_PATH=/ieee-dp-sharing/ npm run build
npm run preview
```

## GitHub Pages setup

Full checklist: [`docs/GITHUB_PAGES_SETUP.md`](docs/GITHUB_PAGES_SETUP.md).

1. Push this repo to GitHub
2. Run **Actions → Deploy to GitHub Pages** once (creates `gh-pages` branch)
3. **Settings → Pages → Deploy from a branch → `gh-pages` / (root)**
4. Site URL: `https://<org>.github.io/<repo>/`

## Daily automation (Actions cron)

[`.github/workflows/daily-pipeline.yml`](.github/workflows/daily-pipeline.yml) runs at **06:00 UTC** (and on manual **Run workflow**):

1. [`scripts/daily-pipeline.sh`](scripts/daily-pipeline.sh) — enrich, validate, build, commit, push
2. Optional LinkedIn staging import (no-op until API secrets set)
3. `scripts/enrich.py` → `scripts/validate.py` → `npm run build`
4. Commit `data/entries.json` and **push**
5. Push triggers **deploy-pages.yml** → updates `gh-pages` → live site

```bash
# Local dry-run
npm run pipeline:dry

# Local build + push (triggers GitHub Actions deploy on push)
./scripts/build-and-push.sh "chore: update showcase"

# Force deploy when data/entries.json did not change
./scripts/build-and-push.sh --force-deploy
```

## Adding an entry manually

Append to the `entries` array in `data/entries.json`:

```json
{
  "id": "jane-doe-example-2026",
  "text": "IEEE DataPort helped our lab publish benchmark data with a citable DOI.",
  "display_name": "Jane Doe",
  "affiliation": "Example University",
  "profile_url": null,
  "source_type": "manual_submission",
  "source_url": null,
  "event": null,
  "society": "IEEE Computer Society",
  "region": "North America",
  "dataset_topic": "Benchmarks",
  "post_type": "testimonial",
  "consent_status": "granted",
  "consent_note": "Written consent on file.",
  "moderation_status": "approved",
  "approved_by": "editor-handle",
  "approved_at": "2026-07-01",
  "submitted_at": "2026-06-28",
  "published_at": "2026-07-01",
  "featured": false,
  "tags": ["citation", "reproducibility"],
  "enrichment": null
}
```

Run `npm run enrich` to populate the `enrichment` block.

## License

Content in `data/entries.json` should only include material with explicit republication consent. Code is provided for IEEE DataPort community use.
