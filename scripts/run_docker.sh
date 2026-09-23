#!/usr/bin/env bash
# Build the CUDA image and run project testcases inside it via docker compose.
# Equivalent to: docker compose --env-file .env -f docker/compose.cuda.yaml build
#                docker compose ... run --rm qiansai ./run.sh <args>
# Exit code follows run.sh: 0 all passed, 1 test failures, 2 environment errors.
set -euo pipefail
qiansai_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$qiansai_root"

usage() {
    printf '%s\n' \
        'Usage: bash scripts/run_docker.sh [--no-build] <run.sh args>' \
        '  e.g. bash scripts/run_docker.sh --case Prob001_zero' \
        '       bash scripts/run_docker.sh --no-build --suite verilogeval-v2' >&2
    exit 2
}

[[ $# -ge 1 ]] || usage
no_build=0
if [[ "$1" == "--no-build" ]]; then
    no_build=1
    shift
fi
[[ $# -ge 1 ]] || usage

if ! command -v docker >/dev/null; then
    printf '%s\n' 'docker is required.' >&2
    exit 2
fi
if docker compose version >/dev/null 2>&1; then
    compose=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    compose=(docker-compose)
else
    printf '%s\n' 'docker compose is required (v2 plugin or docker-compose).' >&2
    exit 2
fi

env_file=.env
compose_file=docker/compose.cuda.yaml
if [[ ! -f "$env_file" ]]; then
    cp .env.example "$env_file"
    printf '%s\n' "Created $env_file from .env.example; set CUDA_VLLM_IMAGE, then retry." >&2
    exit 2
fi
if ! grep -Eq '^CUDA_VLLM_IMAGE=.+' "$env_file"; then
    printf '%s\n' "CUDA_VLLM_IMAGE is empty in $env_file; pin an image (e.g. vllm/vllm-openai:v0.19.1)." >&2
    exit 2
fi
if grep -Eq '^CUDA_VLLM_IMAGE=.*:latest' "$env_file"; then
    printf '%s\n' 'warning: CUDA_VLLM_IMAGE uses :latest; results are not comparable to the pinned baseline.' >&2
fi

# Preflight: fail fast instead of after a long build.
for required in \
    model/weights/chipmate-v-4b/config.json \
    model/weights/chipmate-p-4b/config.json \
    model/weights/download_manifest.json \
    data/processed/verilogeval_v2.jsonl; do
    if [[ ! -f "$required" ]]; then
        printf 'Missing %s; sync weights and data before running.\n' "$required" >&2
        exit 2
    fi
done

if [[ "$no_build" -eq 0 ]]; then
    "${compose[@]}" --env-file "$env_file" -f "$compose_file" build
fi
# -T keeps the run non-interactive so tmux/nohup work; run.sh exit code passes through.
# entrypoint.sh already passes one "--" separator to services.py, which strips a single
# leading "--"; sending another one here made services.py exec the leftover "--".
exec "${compose[@]}" --env-file "$env_file" -f "$compose_file" run -T --rm qiansai ./run.sh "$@"
