import pytest

from agents import reviewer
from agents.state import PipelineState
from graph import route_after_review


@pytest.mark.parametrize("status, expected", [("done", "done"), ("failed", "failed"), ("coding", "coder")])
def test_route_after_review(status, expected):
    assert route_after_review(PipelineState(task_description="t", status=status)) == expected


@pytest.mark.parametrize(
    "approved, iteration_count, expected",
    [(True, 1, "done"), (False, 1, "coding"), (False, 3, "failed"), (True, 3, "done")],
)
def test_reviewer_sets_status(monkeypatch, approved, iteration_count, expected):
    monkeypatch.setattr(reviewer, "ask_json", lambda prompt, schema: schema(approved=approved))
    state = PipelineState(task_description="t", iteration_count=iteration_count, test_passed=True)
    assert reviewer.reviewer_node(state)["status"] == expected


def test_reviewer_cannot_approve_failed_tests(monkeypatch):
    monkeypatch.setattr(reviewer, "ask_json", lambda prompt, schema: schema(approved=True))
    state = PipelineState(task_description="t", iteration_count=1, test_passed=False)
    result = reviewer.reviewer_node(state)
    assert result["approved"] is False
    assert result["status"] == "coding"
    assert "tests failed" in result["review_feedback"]


def test_coder_keeps_every_attempt(monkeypatch):
    from agents import coder

    monkeypatch.setattr(coder, "ask_json", lambda prompt, schema: schema(code="v2", test_code="t", explanation="e"))
    state = PipelineState(task_description="t", code="v1", code_history=["v1"], iteration_count=1, review_feedback="fix it")
    result = coder.coder_node(state)
    assert result["code_history"] == ["v1", "v2"]
    assert result["iteration_count"] == 2
