import logging
import os
import random
import time
from collections import deque
from functools import cache

import httpx
from google import genai
from google.genai import errors, types

from metrics import CIRCUIT_OPEN, LLM_ATTEMPTS, LLM_CALLS, LLM_RETRIES

log = logging.getLogger(__name__)

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
TIMEOUT_MS = 30_000
MAX_ATTEMPTS = 3
BASE_DELAY = 2
MAX_RETRY_DELAY = 60
RETRYABLE_CODES = {429, 500, 502, 503, 504}
# the free tier allows 15 requests/min, so stay under it instead of finding out
# from a 429. counted per worker process. 0 turns it off
MAX_RPM = int(os.getenv("LLM_MAX_RPM", "0"))


class LLMError(Exception):
    pass


class CircuitOpenError(LLMError):
    pass


class CircuitBreaker:
    def __init__(self, threshold=5, cooldown=30):
        self.threshold = threshold
        self.cooldown = cooldown
        self.failures = 0
        self.opened_at = None

    def check(self):
        if self.opened_at is None:
            return
        waited = time.monotonic() - self.opened_at
        if waited < self.cooldown:
            raise CircuitOpenError(f"circuit open, gemini failing (retry in {self.cooldown - waited:.0f}s)")
        # half-open: let one call through, and a single failure reopens it
        self.opened_at = None
        self.failures = self.threshold - 1
        CIRCUIT_OPEN.set(0)

    def record_success(self):
        self.failures = 0

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold and self.opened_at is None:
            self.opened_at = time.monotonic()
            CIRCUIT_OPEN.set(1)
            log.warning("circuit opened after %d failures", self.failures)


# one per worker process, shared by every task that worker runs
breaker = CircuitBreaker()


@cache
def get_client():
    # created on first use so importing the agents doesn't need an API key
    return genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(timeout=TIMEOUT_MS),
    )


_recent_calls = deque()


def _wait_for_rate_limit():
    if not MAX_RPM:
        return
    now = time.monotonic()
    while _recent_calls and now - _recent_calls[0] >= 60:
        _recent_calls.popleft()
    if len(_recent_calls) >= MAX_RPM:
        wait = 60 - (now - _recent_calls[0])
        log.info("rate limit, waiting %.1fs", wait)
        time.sleep(wait)
        _recent_calls.popleft()
    _recent_calls.append(time.monotonic())


def _retry_delay(error, attempt):
    # a 429 says how long to wait (49s when I tested the free tier), so use that
    if isinstance(error, errors.APIError) and error.code == 429 and isinstance(error.details, dict):
        for detail in error.details.get("error", {}).get("details", []):
            if detail.get("@type", "").endswith("RetryInfo") and "retryDelay" in detail:
                return float(detail["retryDelay"].rstrip("s"))
    return BASE_DELAY * 2 ** (attempt - 1) + random.uniform(0, 1)


def _generate(prompt, schema):
    return get_client().models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )


def ask_json(prompt, schema):
    """Call Gemini and return the reply parsed into the pydantic `schema`."""
    try:
        parsed = _ask_with_retries(prompt, schema)
    except Exception:
        LLM_CALLS.labels("failed").inc()
        raise
    LLM_CALLS.labels("success").inc()
    return parsed


def _ask_with_retries(prompt, schema):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        breaker.check()
        _wait_for_rate_limit()
        try:
            response = _generate(prompt, schema)
        except errors.APIError as e:
            if e.code not in RETRYABLE_CODES:
                LLM_ATTEMPTS.labels("client_error").inc()
                raise  # bad key, bad request, unknown model: retrying won't fix it
            LLM_ATTEMPTS.labels("rate_limited" if e.code == 429 else "server_error").inc()
            breaker.record_failure()
            last_error = e
        except httpx.TransportError as e:  # timeouts and dropped connections
            LLM_ATTEMPTS.labels("timeout").inc()
            breaker.record_failure()
            last_error = e
        else:
            # gemini answered, so the service is fine even if the JSON isn't
            breaker.record_success()
            if response.parsed is not None:
                LLM_ATTEMPTS.labels("ok").inc()
                return response.parsed
            LLM_ATTEMPTS.labels("bad_json").inc()
            last_error = LLMError("reply didn't match the schema")

        log.warning("gemini attempt %d/%d failed: %s", attempt, MAX_ATTEMPTS, last_error)
        if attempt < MAX_ATTEMPTS:
            delay = _retry_delay(last_error, attempt)
            if delay > MAX_RETRY_DELAY:
                # usually the daily quota, waiting inside one task won't help
                raise LLMError(f"gemini asked to wait {delay:.0f}s, giving up") from last_error
            LLM_RETRIES.inc()
            time.sleep(delay)

    raise LLMError(f"gemini failed after {MAX_ATTEMPTS} attempts: {last_error}") from last_error
