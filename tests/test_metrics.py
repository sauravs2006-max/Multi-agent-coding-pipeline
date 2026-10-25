from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

import main
from agents import tester
from agents.state import PipelineState
from graph import tracked


def value(name, **labels):
    return REGISTRY.get_sample_value(name, labels) or 0.0


def test_tracked_counts_success_and_time():
    runs = value("pipeline_agent_runs_total", agent="fake", outcome="success")
    timed = value("pipeline_agent_duration_seconds_count", agent="fake")

    assert tracked("fake", lambda state: {"ok": True})(None) == {"ok": True}

    assert value("pipeline_agent_runs_total", agent="fake", outcome="success") == runs + 1
    assert value("pipeline_agent_duration_seconds_count", agent="fake") == timed + 1


def test_tracked_counts_errors_and_reraises():
    def broken(state):
        raise ValueError("boom")

    errors = value("pipeline_agent_runs_total", agent="broken", outcome="error")
    with pytest.raises(ValueError):
        tracked("broken", broken)(None)
    assert value("pipeline_agent_runs_total", agent="broken", outcome="error") == errors + 1
    assert value("pipeline_agent_duration_seconds_count", agent="broken") >= 1  # timed even when it fails


@pytest.mark.parametrize(
    "exit_code, timed_out, oom_killed, result",
    [(0, False, False, "passed"), (1, False, False, "failed"), (124, True, False, "timeout"),
     (137, True, False, "timeout"), (137, False, True, "killed")],
)
def test_sandbox_results_are_counted(monkeypatch, exit_code, timed_out, oom_killed, result):
    run = {"exit_code": exit_code, "stdout": "", "stderr": "", "timed_out": timed_out, "oom_killed": oom_killed}
    monkeypatch.setattr(tester, "run_in_sandbox", lambda code, tests: run)
    before = value("sandbox_runs_total", result=result)
    tester.tester_node(PipelineState(task_description="t", code="x = 1", test_code="assert True"))
    assert value("sandbox_runs_total", result=result) == before + 1


def test_api_labels_requests_by_route_template(monkeypatch):
    monkeypatch.setattr(main.celery_app, "AsyncResult", lambda task_id: SimpleNamespace(state="PENDING"))
    client = TestClient(main.api)
    labels = {"method": "GET", "path": "/tasks/{task_id}", "status": "404"}
    before = value("http_request_duration_seconds_count", **labels)

    client.get("/tasks/some-random-id")

    assert value("http_request_duration_seconds_count", **labels) == before + 1
    assert value("http_request_duration_seconds_count", method="GET", path="/tasks/some-random-id", status="404") == 0


def test_metrics_endpoint():
    response = TestClient(main.api).get("/metrics/")
    assert response.status_code == 200
    assert "pipeline_agent_duration_seconds" in response.text
