from .state import PipelineState
from .breaker import CircuitBreaker, CircuitOpenError
import os

import httpx

from metrics import SANDBOX_RUNS

SANDBOX_URL = os.getenv("SANDBOX_URL", "http://localhost:8080")
TIMEOUT_SECONDS = 10
# the run itself can take TIMEOUT_SECONDS, plus container start, the SIGKILL grace and cleanup
REQUEST_TIMEOUT = TIMEOUT_SECONDS + 20

# only counts the service being down or erroring. code that times out is the code's
# fault and comes back as a normal result, so it never trips this
breaker = CircuitBreaker("sandbox", threshold=3, cooldown=30)


class SandboxError(Exception):
    pass


def run_in_sandbox(code: str, tests: str) -> dict:
    breaker.check()
    payload = {"code": code, "tests": tests, "timeout": TIMEOUT_SECONDS}
    try:
        response = httpx.post(f"{SANDBOX_URL}/run", json=payload, timeout=REQUEST_TIMEOUT)
    except httpx.TransportError as e:  # refused, dns, or no answer in time
        breaker.record_failure()
        raise SandboxError(f"can't reach the sandbox service at {SANDBOX_URL}: {e!r}") from e

    if response.status_code >= 500:
        breaker.record_failure()
        raise SandboxError(f"sandbox service returned {response.status_code}: {response.text[:200]}")
    breaker.record_success()
    response.raise_for_status()  # a 4xx means we sent a bad request, that's a bug here
    return response.json()


def sandbox_result(run: dict) -> str:
    if run["exit_code"] == 0:
        return "passed"
    if run["timed_out"]:
        return "timeout"
    if run["oom_killed"]:
        return "killed"
    return "failed"


def tester_node(state: PipelineState) -> dict:
    if state.test_code.strip():
        try:
            run = run_in_sandbox(state.code, state.test_code)
        except (SandboxError, CircuitOpenError):
            # not the code's fault, so fail the task instead of sending it back to the coder
            SANDBOX_RUNS.labels("unavailable").inc()
            raise
        SANDBOX_RUNS.labels(sandbox_result(run)).inc()
    else:
        run = {"exit_code": 1, "stdout": "", "stderr": "No test_code was provided, so nothing was tested."}
        SANDBOX_RUNS.labels("no_tests").inc()

    test_passed = run["exit_code"] == 0

    return {
        "test_passed": test_passed,
        "test_results": [{"passed": test_passed, "returncode": run["exit_code"]}],
        "stdout": run["stdout"],
        "stderr": run["stderr"],
        "status": "reviewing",
    }
