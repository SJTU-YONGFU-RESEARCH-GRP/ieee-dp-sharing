#!/usr/bin/env bash
# ieee-dp-sharing: daily data refresh → Astro build → git commit + push
#
# Intended for GitHub Actions cron (workflow_dispatch) and local dry-runs.
# A successful push to main/master triggers .github/workflows/deploy-pages.yml.
#
# Steps:
#   [import]  optional LinkedIn API staging (no-op until secrets configured)
#   [merge]   scripts/merge_staging.py — CSV #ieeedataport → entries.json (auto-publish)
#   [enrich]  scripts/enrich.py — sentiment/topics for approved entries
#   [validate] scripts/validate.py
#   [build]   NODE_ENV=production npm run build (GitHub Pages base path)
#   [git]     commit data/ changes and push (unless --no-push)
#
# Usage:
#   ./scripts/daily-pipeline.sh
#   ./scripts/daily-pipeline.sh --dry-run
#   ./scripts/daily-pipeline.sh --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: ./scripts/daily-pipeline.sh [OPTIONS] [COMMIT_MESSAGE]

Options:
  -h, --help         Show this help.
  -n, --dry-run      Print commands only.
  --skip-install     Skip npm ci / npm install.
  --use-install      Run npm install instead of npm ci.
  --no-push          Commit locally but do not push.
  --no-import        Skip LinkedIn staging import step.
  --force-deploy     Update deploy stamp and push even if entries unchanged.
  -v, --verbose      Shell trace (set -x).

Environment:
  GH_PAGES_BASE      Repo subpath for Pages (default: ieee-dp-sharing).
  BASE_PATH          Astro base override (default: /${GH_PAGES_BASE}/).
  AUTO_PUBLISH       Auto-approve new CSV rows (default: true). Set false for manual queue.

EOF
}

DRY_RUN=0
SKIP_INSTALL=0
USE_INSTALL=0
NO_PUSH=0
NO_IMPORT=0
FORCE_DEPLOY=0
COMMIT_MSG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help)
      usage
      exit 0
      ;;
    -n | --dry-run)
      DRY_RUN=1
      shift
      ;;
    --skip-install)
      SKIP_INSTALL=1
      shift
      ;;
    --use-install)
      USE_INSTALL=1
      shift
      ;;
    --no-push)
      NO_PUSH=1
      shift
      ;;
    --no-import)
      NO_IMPORT=1
      shift
      ;;
    --force-deploy)
      FORCE_DEPLOY=1
      shift
      ;;
    -v | --verbose)
      set -x
      shift
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      COMMIT_MSG="$1"
      shift
      ;;
  esac
done

if [[ -z "$COMMIT_MSG" ]]; then
  COMMIT_MSG="chore: daily pipeline $(date -u +%Y-%m-%dT%H:%M:%SZ)"
fi

GH_PAGES_BASE="${GH_PAGES_BASE:-ieee-dp-sharing}"
export BASE_PATH="${BASE_PATH:-/${GH_PAGES_BASE}/}"
export AUTO_PUBLISH="${AUTO_PUBLISH:-true}"

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf 'DRY-RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

die() {
  echo "error: $*" >&2
  exit 1
}

verify_dist() {
  local idx="$REPO_ROOT/dist/index.html"
  [[ -f "$idx" ]] || die "missing $idx — build did not produce dist/"
  local needle="/${GH_PAGES_BASE}/"
  if ! grep -qF "$needle" "$idx" 2>/dev/null; then
    die "dist/index.html missing ${needle} — check astro.config.mjs base vs GH_PAGES_BASE"
  fi
  echo "  dist OK: GitHub Pages paths present (${needle})"
}

if [[ ! -f "$REPO_ROOT/package.json" ]]; then
  die "package.json not found at $REPO_ROOT"
fi

cd "$REPO_ROOT"
echo "==> Pages base: ${BASE_PATH}"
echo "==> repo root: $REPO_ROOT"

if [[ "$NO_IMPORT" -eq 0 ]]; then
  echo "==> [import] LinkedIn API staging (optional)"
  run python3 scripts/linkedin_import.py || true
fi

echo "==> [merge] scripts/merge_staging.py"
run python3 scripts/merge_staging.py

echo "==> [enrich] scripts/enrich.py"
run python3 scripts/enrich.py

echo "==> [validate] scripts/validate.py"
run python3 scripts/validate.py

if [[ "$SKIP_INSTALL" -eq 0 ]]; then
  echo "==> [deps] npm"
  if [[ "$USE_INSTALL" -eq 1 ]]; then
    run npm install
  elif [[ -f package-lock.json ]]; then
    run npm ci
  else
    run npm install
  fi
else
  echo "==> [deps] skipped"
fi

echo "==> [build] NODE_ENV=production npm run build"
run env NODE_ENV=production GH_PAGES_BASE="$GH_PAGES_BASE" BASE_PATH="$BASE_PATH" npm run build

echo "==> [verify] dist/"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "DRY-RUN: verify_dist"
else
  verify_dist
fi

if [[ "$FORCE_DEPLOY" -eq 1 ]]; then
  echo "==> [stamp] force deploy trigger"
  mkdir -p data
  run bash -c "date -u +%Y-%m-%dT%H:%M:%SZ > data/.deploy-stamp"
fi

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Not a git repo — skipping commit/push."
  exit 0
fi

GIT_TOPLEVEL="$(git rev-parse --show-toplevel)"
cd "$GIT_TOPLEVEL"

echo "==> [git] stage data changes"
run git add data/entries.json data/linkedin-staging.csv data/.deploy-stamp data/linkedin-staging.json 2>/dev/null || run git add data/entries.json data/linkedin-staging.csv data/.deploy-stamp

if [[ "$DRY_RUN" -eq 1 ]]; then
  run git status --short
  echo "Dry run finished."
  exit 0
fi

if git diff --cached --quiet && git diff --quiet data/; then
  echo "No data changes to commit."
  if [[ "$FORCE_DEPLOY" -eq 0 ]]; then
    echo "Pipeline OK (site deploys only after a push triggers deploy-pages.yml)."
    echo "Tip: re-run with --force-deploy to push a deploy stamp and trigger CI."
    exit 0
  fi
fi

git config user.name "${GIT_USER_NAME:-github-actions[bot]}"
git config user.email "${GIT_USER_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}"

git commit -m "$COMMIT_MSG" || true

if [[ "$NO_PUSH" -eq 0 ]]; then
  git push
  echo "Done: pushed — deploy-pages.yml will run on push."
else
  echo "Done: committed locally; push skipped (--no-push)."
fi
