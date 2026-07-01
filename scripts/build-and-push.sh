#!/usr/bin/env bash
# Local helper: full site build + optional git push.
#
# Usage:
#   ./scripts/build-and-push.sh
#   ./scripts/build-and-push.sh "docs: update showcase copy"
#   ./scripts/build-and-push.sh --help
#
# For daily data refresh (enrich + validate + push), use:
#   ./scripts/daily-pipeline.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$SCRIPT_DIR/daily-pipeline.sh" --no-import "$@"
