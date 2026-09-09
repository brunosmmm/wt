#!/usr/bin/env bash
# SPEC-0143: serve the product docs site (docs/product via mkdocs.yml).
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run mkdocs serve "$@"
