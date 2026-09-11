#!/usr/bin/env bash
set -euo pipefail
qiansai_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$qiansai_root"
if [[ ! -x .venv/bin/python ]]; then
    printf '%s\n' 'Run uv sync --frozen first (includes pytest).' >&2
    exit 1
fi
export PATH="$qiansai_root/.venv/bin:$PATH"
.venv/bin/python scripts/prepare_data.py --check
exec .venv/bin/python -m pytest "$@"
