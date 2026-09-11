#!/usr/bin/env bash
set -euo pipefail
cd /app
export QIANSAI_SERVE_HOST=0.0.0.0
export PATH="/app/.venv/bin:$PATH"
export NO_PROXY="${NO_PROXY:-${no_proxy:-}},localhost,127.0.0.1,::1"
export no_proxy="$NO_PROXY"
exec .venv/bin/python -m qiansai.services --model-root /models -- "$@"
