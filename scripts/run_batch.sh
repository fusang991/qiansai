#!/usr/bin/env bash
set -euo pipefail
qiansai_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$qiansai_root"
if [[ $# -lt 1 || $# -gt 2 ]]; then
    printf '%s\n' 'Usage: bash scripts/run_batch.sh INPUT_JSONL [LIMIT]' >&2
    exit 2
fi
qiansai_input="$1"
qiansai_run="runs/$(date +%Y%m%d_%H%M%S)_chipmate_4b"
mkdir "$qiansai_run"
mkdir "$qiansai_run/logs"
cp "$qiansai_input" "$qiansai_run/inputs.jsonl"
cp configs/chipmate_4b.yaml "$qiansai_run/config.yaml"
cp configs/serving.yaml "$qiansai_run/serving.yaml"
git rev-parse HEAD > "$qiansai_run/logs/git_head.txt"
git status --porcelain=v1 > "$qiansai_run/logs/git_status.txt"
git submodule status > "$qiansai_run/logs/submodules.txt"
qiansai_args=(--input "$qiansai_run/inputs.jsonl" --out "$qiansai_run/outputs.jsonl")
if [[ $# -eq 2 ]]; then
    qiansai_args+=(--limit "$2")
fi
bash run.sh "${qiansai_args[@]}" 2>&1 | tee "$qiansai_run/logs/runner.log"
