import re
from pathlib import Path

import pytest

from qiansai.datasets import interface_stub, prepare_tasks, read_tasks

ROOT = Path(__file__).resolve().parents[1]


def test_interface_does_not_include_reference_logic():
    source = """// reference logic must not enter generation inputs
module RefModule(input signed [7:0] a, b, output [7:0] y);
assign y = a + b;
endmodule
"""
    stub = interface_stub(source)
    assert "input signed [7:0] a, b" in stub
    assert "module TopModule" in stub
    assert "assign" not in stub
    assert "reference logic" not in stub
    assert stub.endswith("endmodule\n")


def test_unsupported_interface_fails_explicitly():
    with pytest.raises(ValueError, match="ANSI"):
        interface_stub("module RefModule(a); input a; endmodule")


def test_all_official_tasks_have_interface_only_inputs():
    dataset = ROOT / "data/verilog_eval/dataset_spec-to-rtl"
    tasks = prepare_tasks(dataset)
    assert len(tasks) == 156
    assert len({task["task_id"] for task in tasks}) == 156
    for task in tasks:
        assert set(task) == {"task_id", "question", "ref_sv"}
        assert task["question"] == (dataset / f"{task['task_id']}_prompt.txt").read_text().strip()
        assert re.fullmatch(r"module TopModule\s*\(.*?\)\s*;\s*endmodule\s*", task["ref_sv"], re.DOTALL)


def test_duplicate_task_ids_are_rejected(tmp_path):
    data = '{"task_id":"x","question":"q","ref_sv":"module X(); endmodule"}\n'
    path = tmp_path / "tasks.jsonl"
    path.write_text(data + data)
    with pytest.raises(ValueError, match="Duplicate"):
        read_tasks(path)
