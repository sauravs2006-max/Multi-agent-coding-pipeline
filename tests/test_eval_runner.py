from eval import run_eval

TASK = {"id": "e01_fizzbuzz", "difficulty": "easy", "hidden_test": "hidden"}


def fake_sandbox(monkeypatch, exit_codes):
    runs = iter(exit_codes)

    def run_hidden_test(client, sandbox_url, code, hidden_test):
        code = next(runs)
        return {"exit_code": code, "stdout": "", "stderr": "AssertionError: wrong answer" if code else "",
                "timed_out": False, "oom_killed": False}

    monkeypatch.setattr(run_eval, "run_hidden_test", run_hidden_test)


def pipeline_body(status, history, approved):
    return {"status": status, "result": {"code_history": history, "iteration_count": len(history), "approved": approved}}


def test_grades_every_attempt(monkeypatch):
    fake_sandbox(monkeypatch, [1, 0])
    result = run_eval.grade(None, "", TASK, pipeline_body("done", ["v1", "v2"], True), 12.34)
    assert result["attempt_passes"] == [False, True]
    assert not result["passed_first_try"]
    assert result["passed_final"]
    assert result["iterations"] == 2
    assert result["failure"] is None


def test_failure_reason_comes_from_the_hidden_test(monkeypatch):
    fake_sandbox(monkeypatch, [1])
    result = run_eval.grade(None, "", TASK, pipeline_body("done", ["v1"], True), 3)
    assert result["failure"] == "AssertionError: wrong answer"


def test_pipeline_error_has_nothing_to_grade():
    result = run_eval.grade(None, "", TASK, {"status": "error", "error": "gemini asked to wait 3000s"}, 5)
    assert result["iterations"] is None
    assert not result["passed_final"]
    assert "gemini asked to wait" in result["failure"]


def test_summary_counts():
    results = [
        {"difficulty": "easy", "status": "done", "iterations": 1, "approved": True, "passed_first_try": True,
         "passed_final": True, "wall_seconds": 10},
        {"difficulty": "medium", "status": "done", "iterations": 2, "approved": True, "passed_first_try": False,
         "passed_final": True, "wall_seconds": 20, "attempt_passes": [False, True]},
        {"difficulty": "medium", "status": "done", "iterations": 2, "approved": True, "passed_first_try": True,
         "passed_final": True, "wall_seconds": 20, "attempt_passes": [True, True]},
        {"difficulty": "hard", "status": "done", "iterations": 1, "approved": True, "passed_first_try": False,
         "passed_final": False, "wall_seconds": 30},
        {"difficulty": "hard", "status": "error", "iterations": None, "approved": False, "passed_first_try": False,
         "passed_final": False, "wall_seconds": 40},
    ]
    summary = run_eval.summarize(results)
    assert summary["pass_first_try"] == 0.4
    assert summary["pass_within_3"] == 0.6
    assert summary["avg_iterations_to_pass"] == 1.67
    assert summary["false_approvals"] == 1
    assert summary["rejected_correct_attempts"] == 1
    assert summary["pipeline_errors"] == 1
    assert summary["pass_rate_by_difficulty"] == {"easy": 1.0, "medium": 1.0, "hard": 0.0}


def test_spread():
    assert run_eval.spread([0.6, 0.8, 0.7]) == {"mean": 0.7, "min": 0.6, "max": 0.8, "stdev": 0.1}
    assert run_eval.spread([None]) is None
