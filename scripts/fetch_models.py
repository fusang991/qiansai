#!/usr/bin/env python3
"""Download explicitly pinned, authorized HF models; never collect credentials."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qiansai.datasets import sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "model/manifest.json")
    parser.add_argument("--directory", type=Path, default=ROOT / "model/weights")
    args = parser.parse_args()
    models = json.loads(args.manifest.read_text(encoding="utf-8"))["models"]
    for role, model in models.items():
        if not re.fullmatch(r"[0-9a-f]{40}", model.get("revision") or ""):
            parser.error(f"{role}: set an immutable 40-character revision in {args.manifest}")
        if not re.fullmatch(r"[a-z0-9_-]+", model["directory"]):
            parser.error(f"Invalid model directory for {role}")
    from huggingface_hub import snapshot_download

    records = {}
    for role, model in models.items():
        target = args.directory / model["directory"]
        snapshot_download(
            repo_id=model["repo_id"], revision=model["revision"],
            local_dir=target,
        )
        records[role] = {
            "repo_id": model["repo_id"], "revision": model["revision"],
            "files": {
                str(path.relative_to(target)): sha256_file(path)
                for path in sorted(target.rglob("*"))
                if path.is_file() and ".cache" not in path.relative_to(target).parts
            },
        }
    record = args.directory / "download_manifest.json"
    content = json.dumps(records, indent=2) + "\n"
    if record.exists() and record.read_text(encoding="utf-8") != content:
        raise SystemExit("Existing download manifest differs; choose a new --directory")
    if not record.exists():
        with record.open("x", encoding="utf-8") as stream:
            stream.write(content)
    print(f"Recorded downloaded files in {record}")


if __name__ == "__main__":
    main()
