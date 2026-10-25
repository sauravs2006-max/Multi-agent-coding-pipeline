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
