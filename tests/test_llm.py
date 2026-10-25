from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors
from prometheus_client import REGISTRY
from pydantic import BaseModel

from agents import llm


def metric(name, **labels):
    return REGISTRY.get_sample_value(name, labels) or 0.0


class Answer(BaseModel):
    value: int


def api_error(code, retry_delay=None):
    body = {"error": {"code": code, "message": "test", "status": "TEST", "details": []}}
    if retry_delay:
        body["error"]["details"].append({"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay})
    return errors.APIError(code, body)


@pytest.fixture(autouse=True)
def fresh_breaker(monkeypatch):
    monkeypatch.setattr(llm, "breaker", llm.CircuitBreaker(threshold=5, cooldown=30))
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)


def fake_generate(monkeypatch, outcomes):
    """Each call pops the next outcome: an exception to raise or a parsed value to return."""
    calls = []

    def generate(prompt, schema):
        calls.append(prompt)
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(parsed=outcome)

    monkeypatch.setattr(llm, "_generate", generate)
    return calls


def test_returns_parsed_reply(monkeypatch):
    calls = fake_generate(monkeypatch, [Answer(value=1)])
    assert llm.ask_json("p", Answer).value == 1
    assert len(calls) == 1


def test_retries_server_errors_and_timeouts(monkeypatch):
    calls = fake_generate(monkeypatch, [api_error(503), httpx.ReadTimeout("slow"), Answer(value=2)])
    assert llm.ask_json("p", Answer).value == 2
    assert len(calls) == 3


def test_retries_reply_that_does_not_match_schema(monkeypatch):
    calls = fake_generate(monkeypatch, [None, Answer(value=3)])
    assert llm.ask_json("p", Answer).value == 3
    assert len(calls) == 2


def test_client_errors_are_not_retried(monkeypatch):
    calls = fake_generate(monkeypatch, [api_error(400), Answer(value=1)])
    with pytest.raises(errors.APIError):
        llm.ask_json("p", Answer)
    assert len(calls) == 1


def test_gives_up_after_max_attempts(monkeypatch):
    calls = fake_generate(monkeypatch, [api_error(429)] * llm.MAX_ATTEMPTS)
    with pytest.raises(llm.LLMError, match="after 3 attempts"):
        llm.ask_json("p", Answer)
    assert len(calls) == llm.MAX_ATTEMPTS


def test_circuit_opens_and_fails_fast(monkeypatch):
    calls = fake_generate(monkeypatch, [api_error(503)] * 5)
    for _ in range(2):  # 3 + 2 failed attempts hits the threshold of 5
        with pytest.raises(llm.LLMError):
            llm.ask_json("p", Answer)
    assert len(calls) == 5

    with pytest.raises(llm.CircuitOpenError):
        llm.ask_json("p", Answer)
    assert len(calls) == 5  # gemini wasn't called while open


def test_429_waits_as_long_as_gemini_asks(monkeypatch):
    sleeps = []
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    fake_generate(monkeypatch, [api_error(429, retry_delay="49s"), Answer(value=1)])
    assert llm.ask_json("p", Answer).value == 1
    assert sleeps == [49.0]


def test_gives_up_when_asked_to_wait_too_long(monkeypatch):
    calls = fake_generate(monkeypatch, [api_error(429, retry_delay="3600s"), Answer(value=1)])
    with pytest.raises(llm.LLMError, match="asked to wait"):
        llm.ask_json("p", Answer)
    assert len(calls) == 1


def test_rate_limiter_spreads_calls(monkeypatch):
    now = [0.0]
    sleeps = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    monkeypatch.setattr(llm.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(llm.time, "sleep", fake_sleep)
    monkeypatch.setattr(llm, "MAX_RPM", 3)
    monkeypatch.setattr(llm, "_recent_calls", llm.deque())

    for _ in range(3):  # first 3 in the window go straight through
        llm._wait_for_rate_limit()
        now[0] += 1
    assert sleeps == []

    llm._wait_for_rate_limit()  # 4th waits until the first falls out of the 60s window
    assert sleeps == [57.0]


def test_metrics_count_attempts_and_retries(monkeypatch):
    fake_generate(monkeypatch, [api_error(429), httpx.ReadTimeout("slow"), Answer(value=1)])
    before = {
        "rate_limited": metric("llm_attempts_total", result="rate_limited"),
        "timeout": metric("llm_attempts_total", result="timeout"),
        "ok": metric("llm_attempts_total", result="ok"),
        "retries": metric("llm_retries_total"),
        "calls": metric("llm_calls_total", outcome="success"),
    }

    llm.ask_json("p", Answer)

    assert metric("llm_attempts_total", result="rate_limited") == before["rate_limited"] + 1
    assert metric("llm_attempts_total", result="timeout") == before["timeout"] + 1
    assert metric("llm_attempts_total", result="ok") == before["ok"] + 1
    assert metric("llm_retries_total") == before["retries"] + 2
    assert metric("llm_calls_total", outcome="success") == before["calls"] + 1


def test_circuit_gauge(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(llm.time, "monotonic", lambda: now[0])
    for _ in range(5):
        llm.breaker.record_failure()
    assert metric("llm_circuit_open") == 1

    now[0] += 31
    llm.breaker.check()  # half-open
    assert metric("llm_circuit_open") == 0


def test_half_open_after_cooldown(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(llm.time, "monotonic", lambda: now[0])
    breaker = llm.breaker
    for _ in range(5):
        breaker.record_failure()

    with pytest.raises(llm.CircuitOpenError):
        breaker.check()

    now[0] += 31
    breaker.check()  # trial call allowed
    breaker.record_failure()  # one failure in half-open reopens it
    with pytest.raises(llm.CircuitOpenError):
        breaker.check()

    now[0] += 31
    breaker.check()
    breaker.record_success()
    assert breaker.failures == 0
    breaker.check()  # closed again
