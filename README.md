# IEEE DataPort Member Voices

A static showcase website for curated IEEE DataPort member reflections, testimonials, and feedback — hosted on **GitHub Pages** with consent-based moderation and lightweight semantic insights.

> **Positioning:** A curated member-engagement showcase, not a LinkedIn scraper.

## Live workflow

### A — JSON in repo (active)

1. Add or edit entries in [`data/entries.json`](data/entries.json)
2. Or use the [**Submit**](src/pages/submit.astro) page to generate JSON and open a PR
3. Editor sets `moderation_status: "approved"`, `approved_by`, `approved_at`, `published_at`
4. Push to `main` → GitHub Actions builds and deploys the site

### D — LinkedIn API (future, stub ready)

When IEEE obtains approved LinkedIn API access for organization pages:

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
npm run dev        # http://localhost:4321
npm run validate   # check data/entries.json
npm run enrich     # update sentiment/topics for approved entries
npm run build      # output to dist/
```

For local preview matching GitHub Pages subpath:

```bash
BASE_PATH=/ieee-dp-sharing/ npm run build
npm run preview
```

## GitHub Pages setup

Same pattern as [website-trial-v1](https://github.com/SJTU-YONGFU-RESEARCH-GRP/website-trial-v1). Full checklist: [`docs/GITHUB_PAGES_SETUP.md`](docs/GITHUB_PAGES_SETUP.md).

1. Push this repo to GitHub
2. **Settings → Pages → Build and deployment → GitHub Actions**
3. On push to `main`, [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml) builds and deploys
4. Site URL: `https://<org>.github.io/<repo>/`

## Daily automation (Actions cron)

[`.github/workflows/daily-pipeline.yml`](.github/workflows/daily-pipeline.yml) runs at **06:00 UTC** (and on manual **Run workflow**):

1. [`scripts/daily-pipeline.sh`](scripts/daily-pipeline.sh) — same flow as [website-trial-v1 `build-and-push.sh`](https://github.com/SJTU-YONGFU-RESEARCH-GRP/website-trial-v1/blob/main/scripts/build-and-push.sh)
2. Optional LinkedIn staging import (no-op until API secrets set)
3. `scripts/enrich.py` → `scripts/validate.py` → `npm run build`
4. Commit `data/entries.json` and **push**
5. Push triggers **deploy-pages.yml** → live site

```bash
# Local dry-run
npm run pipeline:dry

# Local build + push
./scripts/build-and-push.sh "chore: update showcase"
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
