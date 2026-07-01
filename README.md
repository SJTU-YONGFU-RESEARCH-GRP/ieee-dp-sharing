# IEEE DataPort Member Voices

A static showcase website for curated IEEE DataPort member reflections, testimonials, and feedback — hosted on **GitHub Pages** with consent-based moderation and lightweight semantic insights.

> **Positioning:** A curated member-engagement showcase, not a LinkedIn scraper.

## Live workflow

### LinkedIn `#ieeedataport` intake (active)

1. Editors search LinkedIn for **`#ieeedataport`** and add rows to [`data/linkedin-staging.csv`](data/linkedin-staging.csv)
2. `python3 scripts/merge_staging.py` auto-publishes new rows (`AUTO_PUBLISH=true` by default)
3. Daily pipeline: merge → enrich → push → site deploy

To require manual approval: `AUTO_PUBLISH=false python3 scripts/merge_staging.py --require-approval`

Full guide: [`docs/EDITORIAL_WORKFLOW.md`](docs/EDITORIAL_WORKFLOW.md)

### Member submit + manual JSON

1. [**Submit**](src/pages/submit.astro) page → JSON for a PR, or edit [`data/entries.json`](data/entries.json) directly
2. Approve with `approve_entry.py` or set moderation fields manually

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
| Submit | `/submit/` | Client-side JSON generator + PR instructions |

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
