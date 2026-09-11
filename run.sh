#!/usr/bin/env bash
set -euo pipefail
qiansai_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$qiansai_root"
if [[ ! -x .venv/bin/python ]]; then
    printf '%s\n' 'Run uv sync --frozen first, or use the prepared container.' >&2
    exit 1
fi
exec .venv/bin/python -m qiansai.runner "$@"
