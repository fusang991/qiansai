#!/usr/bin/env bash
set -euo pipefail
cd /app
qiansai_pids=()
cleanup() {
    if [[ ${#qiansai_pids[@]} -gt 0 ]]; then
        kill -TERM "${qiansai_pids[@]}" 2>/dev/null || true
        wait "${qiansai_pids[@]}" 2>/dev/null || true
    fi
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
mapfile -t qiansai_values < <(.venv/bin/python - <<'PY'
import yaml
c = yaml.safe_load(open("configs/serving.yaml"))
r = c["runtime"]
for value in (c["v"]["model"], c["p"]["model"], r["dtype"], r["max_model_len"],
              r["max_num_seqs"], r["gpu_memory_utilization_per_service"]):
    print(value)
PY
)
if [[ ${#qiansai_values[@]} -ne 6 ]]; then
    printf '%s\n' 'Invalid serving configuration.' >&2
    exit 1
fi
for qiansai_role in v p; do
    if [[ ! -f "/models/chipmate-$qiansai_role-4b/config.json" ]]; then
        printf 'Missing model: /models/chipmate-%s-4b\n' "$qiansai_role" >&2
        exit 1
    fi
done
qiansai_common=(--host 0.0.0.0 --dtype "${qiansai_values[2]}"
    --max-model-len "${qiansai_values[3]}" --max-num-seqs "${qiansai_values[4]}"
    --gpu-memory-utilization "${qiansai_values[5]}")
vllm serve /models/chipmate-v-4b --served-model-name "${qiansai_values[0]}" \
    --port 8001 "${qiansai_common[@]}" &
qiansai_pids+=("$!")
vllm serve /models/chipmate-p-4b --served-model-name "${qiansai_values[1]}" \
    --port 8002 "${qiansai_common[@]}" &
qiansai_pids+=("$!")
qiansai_ready=0
for ((qiansai_attempt=0; qiansai_attempt<900; qiansai_attempt++)); do
    for qiansai_pid in "${qiansai_pids[@]}"; do
        if ! kill -0 "$qiansai_pid" 2>/dev/null; then
            printf '%s\n' 'A model server exited during startup. Check container logs.' >&2
            exit 1
        fi
    done
    if .venv/bin/python - <<'PY' 2>/dev/null
from urllib.request import urlopen
for port in (8001, 8002):
    with urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
        assert response.status == 200
PY
    then
        qiansai_ready=1
        break
    fi
    sleep 1
done
if [[ $qiansai_ready -ne 1 ]]; then
    printf '%s\n' 'Timed out waiting for both model services.' >&2
    exit 1
fi
printf '%s\n' 'Both local model services are ready.'
if [[ $# -gt 0 ]]; then
    "$@"
else
    wait -n "${qiansai_pids[@]}"
    exit 1
fi
