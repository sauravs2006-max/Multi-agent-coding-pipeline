import math
import os
import re

from solution import evaluate

cases = {
    "1 + 2 * 3": 7, "(1 + 2) * 3": 9, "-3 + 5": 2, "2 * -3": -6, "-(2 + 3)": -5,
    "10 / 4": 2.5, "2 - 3 - 4": -5, "8 / 4 / 2": 1, "3.5 * 2": 7, "--3": 3, "  7  ": 7,
    "((2))": 2, "1 - -1": 2, "2*(3+4)*5": 70, "0.1 + 0.2": 0.3, "100": 100, "6 / 3 * 2": 4,
    "-2 * -2 * -2": -8, "1 + (2 - (3 + 4)) * 2": -9,
}
for expr, want in cases.items():
    got = evaluate(expr)
    assert isinstance(got, (int, float)), f"evaluate({expr!r}) returned {type(got).__name__}"
    assert math.isclose(got, want, abs_tol=1e-9), f"evaluate({expr!r}) gave {got!r}, expected {want}"

for bad in ("", "   ", "2 +", "(1", "1)", "2 ** 3", "1 2", "abc", "()", "1 + * 2", "3 (4)", "-", "1.2.3"):
    try:
        evaluate(bad)
        raise AssertionError(f"evaluate({bad!r}) should raise ValueError")
    except ValueError:
        pass

for bad in ("1 / 0", "1 / (2 - 2)"):
    try:
        evaluate(bad)
        raise AssertionError(f"evaluate({bad!r}) should raise ZeroDivisionError")
    except ZeroDivisionError:
        pass

# the task is to write the parser, so calling eval/exec/compile doesn't count
# (re.compile and ast.literal_eval are fine)
source = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "solution.py"), encoding="utf-8").read()
assert not re.search(r"(?<![\w.])(eval|exec|compile)\s*\(", source), "solution uses eval, exec or compile"
