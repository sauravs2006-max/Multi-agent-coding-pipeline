import httpx
import pytest
from fastapi.testclient import TestClient

from agents import tester
from agents.breaker import CircuitBreaker, CircuitOpenError
from agents.state import PipelineState
from sandbox.app import app as sandbox_app
from test_sandbox import needs_docker


@pytest.fixture(autouse=True)
def fresh_breaker(monkeypatch):
    monkeypatch.setattr(tester, "breaker", CircuitBreaker("sandbox", threshold=3, cooldown=30))


def fake_post(monkeypatch, response):
    monkeypatch.setattr(tester.httpx, "post", lambda url, json, timeout: response)


@needs_docker
def test_end_to_end_through_the_sandbox_app(monkeypatch):
    client = TestClient(sandbox_app)
    monkeypatch.setattr(tester.httpx, "post", lambda url, json, timeout: client.post("/run", json=json))
    state = PipelineState(task_description="t", code="def add(a, b):\n    return a + b",
                          test_code="from solution import add\nassert add(2, 3) == 5\nprint('ok')")
    result = tester.tester_node(state)
    assert result["test_passed"]
    assert result["stdout"].strip() == "ok"


def test_unreachable_sandbox_is_a_clear_error(monkeypatch):
    monkeypatch.setattr(tester, "SANDBOX_URL", "http://127.0.0.1:1")
    with pytest.raises(tester.SandboxError, match="can't reach the sandbox"):
        tester.run_in_sandbox("x = 1", "pass")


def test_server_error_is_a_sandbox_error(monkeypatch):
    request = httpx.Request("POST", "http://sandbox/run")
    fake_post(monkeypatch, httpx.Response(503, text='{"detail":"docker error"}', request=request))
    with pytest.raises(tester.SandboxError, match="503"):
        tester.run_in_sandbox("x = 1", "pass")


def refuse(url, json, timeout):
    raise httpx.ConnectError("connection refused")


def test_breaker_opens_after_repeated_failures(monkeypatch):
    monkeypatch.setattr(tester.httpx, "post", refuse)
    for _ in range(3):
        with pytest.raises(tester.SandboxError):
            tester.run_in_sandbox("x = 1", "pass")
    with pytest.raises(CircuitOpenError):
        tester.run_in_sandbox("x = 1", "pass")


def test_tester_node_reraises_when_sandbox_is_down(monkeypatch):
    monkeypatch.setattr(tester.httpx, "post", refuse)
    state = PipelineState(task_description="t", code="x = 1", test_code="assert x == 1")
    with pytest.raises(tester.SandboxError):
        tester.tester_node(state)
