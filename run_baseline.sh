#!/usr/bin/env bash
set -euo pipefail
qiansai_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$qiansai_root"
if [[ ! -x .venv/bin/python ]]; then
    printf '%s\n' 'Run uv sync --frozen first, or use the prepared container.' >&2
    exit 1
fi
export PATH="$qiansai_root/.venv/bin:$PATH"
export NO_PROXY="${NO_PROXY:-${no_proxy:-}},localhost,127.0.0.1,::1"
export no_proxy="$NO_PROXY"
exec .venv/bin/python -m qiansai.baseline "$@"
