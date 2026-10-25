from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors
from pydantic import BaseModel

from agents import llm


class Answer(BaseModel):
    value: int


def api_error(code):
    return errors.APIError(code, {"error": {"code": code, "message": "test", "status": "TEST"}})


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
