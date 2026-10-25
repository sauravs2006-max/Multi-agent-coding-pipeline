import logging
import os
import random
import time
from functools import cache

import httpx
from google import genai
from google.genai import errors, types

log = logging.getLogger(__name__)

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
TIMEOUT_MS = 30_000
MAX_ATTEMPTS = 3
BASE_DELAY = 2
RETRYABLE_CODES = {429, 500, 502, 503, 504}


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

    def record_success(self):
        self.failures = 0

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold and self.opened_at is None:
            self.opened_at = time.monotonic()
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
    for attempt in range(1, MAX_ATTEMPTS + 1):
        breaker.check()
        try:
            response = _generate(prompt, schema)
        except errors.APIError as e:
            if e.code not in RETRYABLE_CODES:
                raise  # bad key, bad request, unknown model: retrying won't fix it
            breaker.record_failure()
            last_error = e
        except httpx.TransportError as e:  # timeouts and dropped connections
            breaker.record_failure()
            last_error = e
        else:
            # gemini answered, so the service is fine even if the JSON isn't
            breaker.record_success()
            if response.parsed is not None:
                return response.parsed
            last_error = LLMError("reply didn't match the schema")

        log.warning("gemini attempt %d/%d failed: %s", attempt, MAX_ATTEMPTS, last_error)
        if attempt < MAX_ATTEMPTS:
            time.sleep(BASE_DELAY * 2 ** (attempt - 1) + random.uniform(0, 1))

    raise LLMError(f"gemini failed after {MAX_ATTEMPTS} attempts: {last_error}") from last_error
