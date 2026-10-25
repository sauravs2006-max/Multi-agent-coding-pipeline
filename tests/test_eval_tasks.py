import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TASKS_DIR = Path(__file__).parent.parent / "eval" / "tasks"
TASKS = sorted(p.name for p in TASKS_DIR.iterdir() if p.is_dir())


def run_hidden_test(tmp_path, task, solution_source):
    # same file names the sandbox uses, so the hidden test imports `solution`
    (tmp_path / "solution.py").write_text(solution_source, encoding="utf-8")
    shutil.copy(TASKS_DIR / task / "hidden_test.py", tmp_path / "test_solution.py")
    return subprocess.run([sys.executable, "test_solution.py"], cwd=tmp_path,
                          capture_output=True, text=True, timeout=60)


def test_there_are_15_tasks():
    difficulties = [t[0] for t in TASKS]
    assert (difficulties.count("e"), difficulties.count("m"), difficulties.count("h")) == (5, 6, 4)


@pytest.mark.parametrize("task", TASKS)
def test_reference_passes_hidden_test(tmp_path, task):
    reference = (TASKS_DIR / task / "reference.py").read_text(encoding="utf-8")
    result = run_hidden_test(tmp_path, task, reference)
    assert result.returncode == 0, result.stderr[-1000:]


@pytest.mark.parametrize("task", TASKS)
def test_hidden_test_fails_without_a_solution(tmp_path, task):
    assert run_hidden_test(tmp_path, task, "").returncode != 0


@pytest.mark.parametrize("task", TASKS)
def test_prompt_exists(task):
    assert (TASKS_DIR / task / "prompt.txt").read_text(encoding="utf-8").strip()
