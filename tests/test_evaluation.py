from pathlib import Path
import shutil

import pytest

from qiansai.evaluation import evaluate, simulation_result

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/verilog_eval/dataset_spec-to-rtl"


@pytest.mark.parametrize("output,code,timed_out,reason", [
    ("", 0, False, "missing_or_ambiguous_testbench_summary"),
    ("Mismatches: 0 in 0 samples\n", 0, False, "no_samples"),
    ("Mismatches: 0 in 20 samples\nTIMEOUT\n", 0, False, "testbench_timeout"),
    ("Mismatches: 0 in 20 samples\n", 1, False, "simulation_error"),
    ("Mismatches: 0 in 20 samples\n", 0, True, "simulation_wall_timeout"),
    ("Mismatches: 0 in 20 samples\n" * 2, 0, False, "missing_or_ambiguous_testbench_summary"),
])
def test_incomplete_or_failed_simulation_cannot_pass(output, code, timed_out, reason):
    result = simulation_result(output, code, timed_out)
    assert result["status"] == "FAIL"
    assert result["reason"] == reason


@pytest.mark.skipif(
    not all(shutil.which(t) for t in ("iverilog", "vvp")), reason="Icarus is required",
)
@pytest.mark.parametrize("body,compile_status,simulation_status", [
    ("assign zero=1'b0;", "PASS", "PASS"),
    ("assign zero=1'b1;", "PASS", "FAIL"),
    ("invalid syntax;", "FAIL", "NOT_RUN"),
    ("initial $finish;", "PASS", "FAIL"),
])
def test_official_testbench_classifies_candidate(tmp_path, body, compile_status, simulation_status):
    candidate = tmp_path / "candidate.sv"
    candidate.write_text(f"module TopModule(output zero); {body} endmodule\n")
    result = evaluate(
        candidate, DATA / "Prob001_zero_ref.sv", DATA / "Prob001_zero_test.sv",
        tmp_path / "evaluation",
    )
    assert result["compile"]["status"] == compile_status
    assert result["simulation"]["status"] == simulation_status
    assert result["status"] == ("PASS" if simulation_status == "PASS" else "FAIL")
    assert (tmp_path / "evaluation/compile.log").exists()
    with pytest.raises(FileExistsError):
        evaluate(candidate, DATA / "Prob001_zero_ref.sv", DATA / "Prob001_zero_test.sv",
                 tmp_path / "evaluation")
