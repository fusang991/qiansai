from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Thread

import pytest
import yaml

from qiansai.case_runner import select_tasks
from qiansai.services import ModelServices

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("cases,limit", [
    (["missing"], None), (["one", "one"], None), (None, 0),
])
def test_invalid_selection_is_rejected(cases, limit):
    with pytest.raises(ValueError):
        select_tasks([{"task_id": "one"}], cases, limit)


@pytest.mark.parametrize("bit,expected,exit_code", [(0, "PASS", 0), (1, "FAIL", 1)])
def test_cli_cross_agreement_does_not_replace_official_evaluation(tmp_path, bit, expected, exit_code):
    """Synthetic HTTP responders exercise the real workflow; this is a CPU test."""
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, body):
            content = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            role = self.path.split("/")[1].upper()
            self.reply({"data": [{"id": f"core12345/ChipMATE-{role}-4B"}]})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            fence = chr(96) * 3
            if body["model"].endswith("-V-4B"):
                text = f"{fence}verilog\nmodule TopModule(output zero); assign zero=1'b{bit}; endmodule\n{fence}"
            else:
                text = f"{fence}python\nclass TopModule:\n def eval(self, inputs): return {{'zero': {bit}}}\n{fence}"
            self.reply({
                "id": "cpu-fixture", "object": "chat.completion", "created": 0,
                "model": body["model"],
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": text}}],
            })

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    config = yaml.safe_load((ROOT / "configs/serving.yaml").read_text())
    for role in ("v", "p"):
        config[role]["base_url"] = f"http://127.0.0.1:{server.server_port}/{role}/v1"
    serving = tmp_path / "serving.yaml"
    serving.write_text(yaml.safe_dump(config))
    output = tmp_path / "run"
    # A cloud SSH session can have a missing or unrelated python3 on PATH.
    unrelated = tmp_path / "unrelated_bin"
    unrelated.mkdir()
    (unrelated / "python3").write_text("#!/bin/sh\nexit 91\n")
    (unrelated / "python3").chmod(0o755)
    environment = {
        **os.environ, "PATH": str(unrelated) + os.pathsep + os.environ["PATH"],
        "HTTP_PROXY": "http://127.0.0.1:1", "HTTPS_PROXY": "http://127.0.0.1:1",
        "http_proxy": "http://127.0.0.1:1", "https_proxy": "http://127.0.0.1:1",
        "NO_PROXY": "", "no_proxy": "",
    }
    try:
        result = subprocess.run([
            "bash", str(ROOT / "run.sh"), "--case", "Prob001_zero",
            "--serving", str(serving), "--no-start", "--run-dir", str(output),
        ], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    assert result.returncode == exit_code, result.stdout + result.stderr
    metrics = json.loads((output / "metrics.json").read_text())
    task = metrics["tasks"][0]
    assert task["status"] == expected
    assert task["cross_verification_match_rate"] == 1.0
    assert task["compile"] == "PASS"
    assert task["simulation"] == expected
    assert len(requests) == 6
    assert len(list(output.glob("tasks/*/calls/*/batch_*/response.json"))) == 2
    inputs = json.loads((output / "inputs.jsonl").read_text())
    assert "assign" not in inputs["ref_sv"]
    assert (output / "tasks/Prob001_zero/evaluation/simulation.log").is_file()
    retry = subprocess.run([
        sys.executable, "-m", "qiansai.runner", "--case", "Prob001_zero",
        "--no-start", "--run-dir", str(output),
    ], cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert retry.returncode == 2
    assert json.loads((output / "metrics.json").read_text()) == metrics


def test_service_startup_timeout_cleans_up_owned_processes(tmp_path, monkeypatch):
    monkeypatch.setattr("qiansai.services.model_ready", lambda endpoint: False)
    monkeypatch.setattr(ModelServices, "_command",
                        lambda self, role: [sys.executable, "-c", "import time; time.sleep(60)"])
    services = ModelServices(
        {"v": {"model": "v"}, "p": {"model": "p"}, "runtime": {}},
        tmp_path, tmp_path / "logs", startup_timeout=0.01,
    )
    with pytest.raises(RuntimeError, match="timed out"):
        with services:
            pass
    assert services.processes
    assert all(process.poll() is not None for process in services.processes)
    assert all(stream.closed for stream in services.streams)
