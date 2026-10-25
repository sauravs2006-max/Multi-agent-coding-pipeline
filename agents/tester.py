from .state import PipelineState
import os
import tempfile

import docker
import requests
from docker.types import LogConfig

from metrics import SANDBOX_RUNS

SANDBOX_IMAGE = "python:3.11-slim"
TIMEOUT_SECONDS = 10
MAX_OUTPUT_CHARS = 4000
CODE_FILE = "solution.py"
TEST_FILE = "test_solution.py"

# docker keeps at most 1 MB of logs per container, so "print forever" can't fill memory
LOG_CONFIG = LogConfig(type=LogConfig.types.JSON, config={"max-size": "1m", "max-file": "1"})


class SandboxError(Exception):
    pass


def trim(text: str) -> str:
    # keep the end, that's where the traceback and final results are
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return "[output truncated]\n" + text[-MAX_OUTPUT_CHARS:]


def run_in_sandbox(code: str, tests: str, timeout: int = TIMEOUT_SECONDS) -> dict:
    """Run the tests against the code in a throwaway container."""
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        # not the code's fault, so fail the task instead of sending it back to the coder
        raise SandboxError("can't reach docker, is Docker Desktop running?") from e

    with tempfile.TemporaryDirectory() as tmp_dir:
        for name, content in ((CODE_FILE, code), (TEST_FILE, tests)):
            with open(os.path.join(tmp_dir, name), "w", encoding="utf-8") as f:
                f.write(content)

        # SIGTERM at the timeout, SIGKILL 2s later if the code ignores it
        command = ["timeout", "-k", "2", str(timeout), "python", f"/code/{TEST_FILE}"]
        container = client.containers.run(
            SANDBOX_IMAGE,
            command,
            volumes={tmp_dir: {"bind": "/code", "mode": "ro"}},
            network_disabled=True,
            mem_limit="128m",
            memswap_limit="128m",  # otherwise it gets another 128m of swap
            pids_limit=64,  # fork bombs
            user="nobody",
            cap_drop=["ALL"],
            security_opt=["no-new-privileges"],
            log_config=LOG_CONFIG,
            detach=True,  # so stdout can still be read after a crash
        )
        try:
            try:
                exit_code = container.wait(timeout=timeout + 10)["StatusCode"]
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                # backstop, the timeout inside the container should always fire first
                container.kill()
                exit_code = 137
            container.reload()
            oom_killed = container.attrs["State"]["OOMKilled"]
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
        finally:
            container.remove(force=True)
            client.close()

    # 137 without an OOM kill means it ignored SIGTERM and got SIGKILLed at the timeout
    timed_out = exit_code == 124 or (exit_code == 137 and not oom_killed)
    if oom_killed:
        stderr += "\nKilled: out of memory (128 MB limit)"
    elif timed_out:
        stderr += f"\nTimed out after {timeout}s"

    return {
        "exit_code": exit_code,
        "stdout": trim(stdout),
        "stderr": trim(stderr),
        "timed_out": timed_out,
        "oom_killed": oom_killed,
    }


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
        run = run_in_sandbox(state.code, state.test_code)
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
