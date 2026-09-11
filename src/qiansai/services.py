"""Manage local inference processes through a GPU-independent HTTP interface."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

import yaml

ROOT = Path(__file__).resolve().parents[2]


def model_ready(endpoint: dict) -> bool:
    try:
        base_url = endpoint["base_url"].rstrip("/")
        with urlopen(base_url.rsplit("/", 1)[0] + "/health", timeout=2):
            pass
        with urlopen(base_url + "/models", timeout=2) as response:
            models = json.load(response)
    except HTTPError as error:
        if error.code in (502, 503):
            return False
        raise RuntimeError(f"Inference endpoint returned HTTP {error.code}: {endpoint['base_url']}") from error
    except (URLError, TimeoutError, ConnectionError):
        return False
    if endpoint["model"] not in {row.get("id") for row in models.get("data", [])}:
        raise RuntimeError(f"Endpoint does not serve the configured model: {endpoint['model']}")
    return True


class ModelServices:
    """Reuse matching services, or launch and clean up only processes we own."""

    def __init__(
        self, config: dict, model_root: Path, logs: Path, *,
        autostart: bool = True, startup_timeout: float = 900,
    ):
        self.config = config
        self.model_root = model_root.resolve()
        self.logs = logs
        self.autostart = autostart
        self.startup_timeout = startup_timeout
        self.processes: list[subprocess.Popen] = []
        self.streams = []
        self.info = {}

    def _command(self, role: str) -> list[str]:
        endpoint, runtime = self.config[role], self.config["runtime"]
        url = urlsplit(endpoint["base_url"])
        if url.hostname not in ("127.0.0.1", "localhost", "::1"):
            raise RuntimeError(f"Cannot automatically start a remote endpoint: {endpoint['base_url']}")
        if url.scheme != "http" or url.username or url.password:
            raise ValueError("Local autostart requires an unauthenticated http endpoint")
        manifest = json.loads((ROOT / "model/manifest.json").read_text())
        entry = manifest["models"][role]
        if endpoint["model"] != entry["repo_id"]:
            raise ValueError(f"Serving model and weight manifest disagree for role {role}")
        directory = self.model_root / entry["directory"]
        if not (directory / "config.json").is_file():
            raise RuntimeError(
                f"Missing {role.upper()} model weights: {directory}. "
                "Obtain HF access and run .venv/bin/python scripts/fetch_models.py"
            )
        index = directory / "model.safetensors.index.json"
        shards = (
            set(json.loads(index.read_text())["weight_map"].values())
            if index.is_file() else {"model.safetensors"}
        )
        if not all((directory / name).is_file() for name in shards):
            raise RuntimeError(f"Incomplete model download: {directory}")
        downloaded = self.model_root / "download_manifest.json"
        if not downloaded.is_file():
            raise RuntimeError(f"Missing weight identity record: {downloaded}")
        identity = json.loads(downloaded.read_text()).get(role, {})
        if any(identity.get(key) != entry[key] for key in ("repo_id", "revision")):
            raise RuntimeError(f"Downloaded weight revision differs from the pinned manifest: {role}")
        local_vllm = ROOT / ".venv-vllm/bin/vllm"
        executable = os.environ.get("QIANSAI_VLLM_EXECUTABLE") or (
            str(local_vllm) if local_vllm.is_file() else shutil.which("vllm")
        )
        executable = shutil.which(executable) if executable else None
        if not executable:
            raise RuntimeError("vLLM is unavailable; prepare the dedicated GPU environment")
        command = [
            executable, "serve", str(directory), "--served-model-name", endpoint["model"],
            "--host", os.environ.get("QIANSAI_SERVE_HOST", "127.0.0.1"),
            "--port", str(url.port or 80), "--dtype", str(runtime["dtype"]),
            "--max-model-len", str(runtime["max_model_len"]),
            "--max-num-seqs", str(runtime["max_num_seqs"]),
            "--gpu-memory-utilization", str(runtime["gpu_memory_utilization_per_service"]),
        ]
        command.extend(str(value) for value in runtime.get("extra_args", []))
        return command

    def __enter__(self):
        try:
            missing = [role for role in ("v", "p") if not model_ready(self.config[role])]
            if missing and not self.autostart:
                raise RuntimeError("Both configured model endpoints must be ready with --no-start")
            # Validate both downloads before consuming GPU resources.
            commands = {role: self._command(role) for role in missing}
            self.logs.mkdir(parents=True, exist_ok=True)
            environment = os.environ.copy()
            environment.update({
                "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                "VLLM_NO_USAGE_STATS": "1", "PYTHONUNBUFFERED": "1",
            })
            environment.update({k: str(v) for k, v in self.config["runtime"].get("environment", {}).items()})
            for key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
                environment.pop(key, None)
            # Sequential startup avoids simultaneous vLLM memory profiling on one GPU.
            for role in ("v", "p"):
                if role not in commands:
                    self.info[role] = {"mode": "reused", "model": self.config[role]["model"]}
                    continue
                command = commands[role]
                log = self.logs / f"serve_{role}.log"
                stream = log.open("x")
                self.streams.append(stream)
                print(f"Starting {role.upper()} model; log: {log}", flush=True)
                started = time.monotonic()
                service_environment = {
                    **environment,
                    "PATH": str(Path(command[0]).parent) + os.pathsep + environment.get("PATH", ""),
                }
                process = subprocess.Popen(
                    command, cwd=ROOT, env=service_environment, stdout=stream,
                    stderr=subprocess.STDOUT, start_new_session=True,
                )
                self.processes.append(process)
                while not model_ready(self.config[role]):
                    self.check()
                    if time.monotonic() - started > self.startup_timeout:
                        raise RuntimeError(f"{role.upper()} startup timed out; see {log}")
                    time.sleep(1)
                self.info[role] = {
                    "mode": "started", "model": self.config[role]["model"],
                    "command": command, "startup_seconds": time.monotonic() - started,
                }
                print(f"{role.upper()} model ready.", flush=True)
            self.check()
            return self
        except BaseException:
            self.close()
            raise

    def check(self):
        for process in self.processes:
            if process.poll() is not None:
                raise RuntimeError(f"A model service exited ({process.returncode}); see {self.logs}")

    def close(self):
        for process in reversed(self.processes):
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                pass
            finally:
                # An exited API process can still leave an engine child behind.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
        for stream in self.streams:
            stream.close()

    def __exit__(self, *args):
        self.close()


def main():
    parser = argparse.ArgumentParser(description="Serve both pinned ChipMATE models")
    parser.add_argument("--serving", type=Path, default=ROOT / "configs/serving.yaml")
    parser.add_argument("--model-root", type=Path, default=Path(os.environ.get("MODEL_ROOT", ROOT / "model/weights")))
    parser.add_argument("--logs", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.logs is None:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        import uuid
        stamp = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")
        args.logs = ROOT / "runs" / f"{stamp}_services_{uuid.uuid4().hex[:8]}" / "logs"
    config = yaml.safe_load(args.serving.read_text())
    def terminate(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, terminate)
    try:
        with ModelServices(config, args.model_root, args.logs) as services:
            print("Both local model services are ready.", flush=True)
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            if command:
                raise SystemExit(subprocess.call(command))
            while True:
                services.check()
                time.sleep(1)
    except KeyboardInterrupt:
        raise SystemExit(130)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(2, f"Service error: {error}\n")


if __name__ == "__main__":
    main()
