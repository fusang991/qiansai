#!/usr/bin/env python3
"""Convert the pinned official dataset to interface-only ChipMATE inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qiansai.datasets import prepare_tasks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/verilog_eval/dataset_spec-to-rtl")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/verilogeval_v2.jsonl")
    parser.add_argument("--check", action="store_true", help="Validate without writing")
    args = parser.parse_args()
    tasks = prepare_tasks(args.dataset)
    encoded = "".join(json.dumps(task, ensure_ascii=False) + "\n" for task in tasks)
    revision = subprocess.check_output(
        ["git", "-C", str(args.dataset), "rev-parse", "HEAD"], text=True,
    ).strip()
    manifest = {
        "dataset_revision": revision,
        "task": "spec-to-rtl",
        "count": len(tasks),
        "input_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        "reference_body_in_generation_input": False,
    }
    if not args.check:
        manifest_path = args.output.with_suffix(".manifest.json")
        payloads = {
            args.output: encoded,
            manifest_path: json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        }
        for path, content in payloads.items():
            if path.exists() and path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Existing content differs; use a new --output path: {path}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        for path, content in payloads.items():
            if not path.exists():
                with path.open("x", encoding="utf-8") as stream:
                    stream.write(content)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
