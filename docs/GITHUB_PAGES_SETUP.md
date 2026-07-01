# Host IEEE DataPort Voices on GitHub Pages

Same deployment model as [website-trial-v1](https://github.com/SJTU-YONGFU-RESEARCH-GRP/website-trial-v1).

## Live URL (after deploy)

**`https://<org>.github.io/<repo>/`**

Example if repo is `ieee-dp-sharing` under `SJTU-YONGFU-RESEARCH-GRP`:

**`https://sjtu-yongfu-research-grp.github.io/ieee-dp-sharing/`**

## One-time GitHub configuration

1. Push this repository to GitHub.

2. Commit **`package-lock.json`** (CI uses **`npm ci`**).

3. **Settings → Pages → Build and deployment → Source: GitHub Actions**

4. Push to **`main`**. Workflow **Deploy to GitHub Pages** (`.github/workflows/deploy-pages.yml`) builds and deploys **`dist/`**.

## Daily automation (website-trial-v1 style)

Workflow **Daily pipeline** (`.github/workflows/daily-pipeline.yml`):

| Trigger | When |
|---------|------|
| `cron: 0 6 * * *` | Every day at 06:00 UTC |
| `workflow_dispatch` | Manual run from Actions tab |

Pipeline steps (`scripts/daily-pipeline.sh`):

```text
LinkedIn staging import (optional, no-op until API secrets set)
        ↓
scripts/enrich.py
        ↓
scripts/validate.py
        ↓
npm ci + npm run build
        ↓
git commit data/entries.json + push
        ↓
push triggers deploy-pages.yml → live site
```

### Manual trigger

**Actions → Daily pipeline → Run workflow**

### Local dry-run

```bash
npm run pipeline:dry
# or
./scripts/daily-pipeline.sh --dry-run
```

### Local full run (commits + pushes)

```bash
./scripts/build-and-push.sh "chore: refresh showcase data"
```

## Repo layout

```text
ieee-dp-sharing/           ← Git repo root
  .github/workflows/
    deploy-pages.yml       ← deploy on push
    daily-pipeline.yml     ← daily cron + manual
  data/entries.json        ← curated testimonials
  scripts/
    daily-pipeline.sh
    enrich.py
    validate.py
  src/                     ← Astro site
```

## Local check before push

```bash
npm ci
npm run validate
NODE_ENV=production GH_PAGES_BASE=ieee-dp-sharing npm run build
npm run preview
```

Open **`http://localhost:4321/ieee-dp-sharing/`** after preview (match your repo name).

`astro.config.mjs` sets **`base: "/{repo}/"`** in production so assets load correctly on project Pages.

## Optional LinkedIn API (future)

Add repository secrets:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_ORG_URN`

Implement `fetch_organization_posts()` in `scripts/linkedin_import.py`. Staged rows land in `data/linkedin-staging.json` for editorial review before merge into `data/entries.json`.

## Troubleshooting

### Blank page / 404 assets

DevTools → Network: if `.js` files 404, `GH_PAGES_BASE` / `BASE_PATH` must match the repo name in the URL. Rebuild and redeploy.

### Deploy job 404

**Settings → Pages → Source** must be **GitHub Actions**, not “Deploy from a branch”.

### Daily pipeline does not push

- Workflow needs **contents: write** (configured in `daily-pipeline.yml`).
- If `data/entries.json` unchanged after enrich, no commit is created (expected).
