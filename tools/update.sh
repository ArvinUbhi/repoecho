#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
uv run --no-project --no-config --python 3.12 --script "$source_dir/.github/skills/repoecho/scripts/update_repoecho.py" "$@"
