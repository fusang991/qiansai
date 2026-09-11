import shutil

import pytest

from chipmate.cross_verify import cross_verify

pytestmark = pytest.mark.skipif(
    not all(shutil.which(tool) for tool in ("iverilog", "vvp")),
    reason="Icarus Verilog and vvp are required for the CPU integration check",
)


@pytest.mark.parametrize("expression,expected", [
    ("i['a'] & i['b']", True),
    ("0", False),
])
def test_cpu_cross_verification_detects_agreement_and_disagreement(expression, expected):
    ports = "module TopModule(input a, input b, output y); endmodule"
    verilog = "module TopModule(input a, input b, output y); assign y=a&b; endmodule"
    python = f"class TopModule:\n def eval(self, i): return {{'y': {expression}}}\n"
    result = cross_verify(ports, verilog, python, num_tests=32, seed=42)
    assert result["sv_error"] is None
    assert result["py_error"] is None
    assert (result["match_rate"] == 1.0) is expected
