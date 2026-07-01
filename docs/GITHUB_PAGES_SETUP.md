# Host IEEE DataPort Voices on GitHub Pages

## Live URL (after deploy)

**`https://<org>.github.io/<repo>/`**

Example if the repository is named `ieee-dp-sharing`:

**`https://<your-org>.github.io/ieee-dp-sharing/`**

## One-time GitHub configuration

1. Push this repository to GitHub.

2. Commit **`package-lock.json`** (CI uses **`npm ci`**).

3. Run **Actions → Deploy to GitHub Pages → Run workflow** once (or push to `main`).  
   This creates/updates the **`gh-pages`** branch with the built site.

4. **Settings → Pages → Build and deployment**
   - **Source:** `Deploy from a branch`
   - **Branch:** `gh-pages`
   - **Folder:** `/ (root)`
   - Save

5. Wait 1–3 minutes, then open your site URL.

> **Note:** This repo uses **branch deploy** (`peaceiris/actions-gh-pages`), not the GitHub Actions Pages API. You do **not** need Source = “GitHub Actions”.

## Daily automation

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
push triggers deploy-pages.yml → gh-pages branch → live site
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

### `configure-pages` / `deploy-pages` / `Get Pages site failed`

Older workflow versions used the **GitHub Actions Pages API**, which fails with 404 until Pages is enabled for Actions. The current workflow **publishes to the `gh-pages` branch** instead and does not call that API.

If you still see this error, re-run after the latest `deploy-pages.yml` is on `main`.

### Site returns 404 in the browser

1. **Workflow succeeded** — check **Actions → Deploy to GitHub Pages** is green.
2. **`gh-pages` branch exists** — it is created by the deploy workflow.
3. **Pages source** — **Settings → Pages → Deploy from a branch → `gh-pages` → `/ (root)`**.
4. **Repository visibility** — on GitHub Free, public `*.github.io` URLs require a **public** repository.

Local `./scripts/build-and-push.sh` **does not upload `dist/` directly**. It only pushes `data/` changes; GitHub Actions builds and publishes `dist/` to `gh-pages`.

To force a deploy when entries are unchanged:

```bash
./scripts/build-and-push.sh --force-deploy
```

### Blank page / 404 assets

DevTools → Network: if `.js` files 404, `GH_PAGES_BASE` / `BASE_PATH` must match the repo name in the URL. Rebuild and redeploy.

### Daily pipeline does not push

- Workflow needs **contents: write** (configured in `daily-pipeline.yml`).
- If `data/entries.json` unchanged after enrich, use `--force-deploy`.
