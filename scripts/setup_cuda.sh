#!/usr/bin/env bash
# Use inside a CUDA-capable cloud container or on a prepared NVIDIA host.
set -euo pipefail
qiansai_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$qiansai_root"
qiansai_index="${QIANSAI_PYPI_INDEX:-https://pypi.org/simple}"
qiansai_python="${QIANSAI_PYTHON:-python3.12}"
if ! command -v uv >/dev/null; then
    printf '%s\n' 'Install uv 0.9.18 first.' >&2
    exit 1
fi
for qiansai_tool in iverilog vvp nvidia-smi; do
    if ! command -v "$qiansai_tool" >/dev/null; then
        printf 'Missing deployment prerequisite: %s\n' "$qiansai_tool" >&2
        exit 1
    fi
done
uv sync --frozen --python "$qiansai_python"
if [[ ! -x .venv-vllm/bin/python ]]; then
    uv venv --python "$qiansai_python" .venv-vllm
fi
uv pip install --python .venv-vllm/bin/python --index-url "$qiansai_index" \
    --require-hashes -r docker/requirements.cuda.lock
uv pip check --python .venv-vllm/bin/python
.venv/bin/python scripts/prepare_data.py
bash scripts/smoke_test.sh -q
printf '%s\n' 'CUDA environment prepared. Authorize and download both weights before the first run.'
