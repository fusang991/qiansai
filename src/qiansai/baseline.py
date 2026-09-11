"""One direct V-model completion per task, without skills, tools, or retries."""

from __future__ import annotations

import json
import time

from chipmate.prompts import extract_verilog
from openai import OpenAI

from .datasets import read_tasks
from .runner import parser, settings


def main() -> None:
    args = parser("Generate directly with the same V-4B inference service").parse_args()
    workflow, serving = settings(args)
    tasks = read_tasks(args.input)
    if args.limit is not None:
        tasks = tasks[:args.limit]
    client = OpenAI(
        api_key="local", base_url=serving["v"]["base_url"], max_retries=0, timeout=900,
    )
    errors = 0
    with args.out.open("x", encoding="utf-8") as output:
        for task in tasks:
            start = time.monotonic()
            row = {"task_id": task["task_id"], "verilog": ""}
            try:
                response = client.chat.completions.create(
                    model=serving["v"]["model"],
                    messages=[{"role": "user", "content": task["question"]}],
                    temperature=workflow["temperature"],
                    top_p=0.95,
                    max_tokens=4096,
                )
                raw = response.choices[0].message.content or ""
                row.update(verilog=extract_verilog(raw), response=response.model_dump())
            except Exception as error:
                errors += 1
                row["error"] = str(error)
            row["wall_seconds"] = time.monotonic() - start
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
