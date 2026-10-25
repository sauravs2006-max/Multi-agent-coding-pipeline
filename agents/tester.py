from .state import PipelineState
import os
import tempfile

import docker

SANDBOX_IMAGE = "python:3.11-slim"
TIMEOUT_SECONDS = 10
MAX_OUTPUT_CHARS = 4000
CODE_FILE = "solution.py"
TEST_FILE = "test_solution.py"


class SandboxError(Exception):
    pass


def run_in_sandbox(files: dict[str, str], script: str) -> tuple[int, str, str]:
    """Write `files` to a temp dir and run `script` in a throwaway container. Returns (returncode, stdout, stderr)."""
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        # not the code's fault, so fail the task instead of sending it back to the coder
        raise SandboxError("can't reach docker, is Docker Desktop running?") from e

    with tempfile.TemporaryDirectory() as tmp_dir:
        for name, content in files.items():
            with open(os.path.join(tmp_dir, name), "w", encoding="utf-8") as f:
                f.write(content)

        # run() with remove=True blocks with no timeout, so the limit is enforced
        # inside the container. -k sends SIGKILL if the code ignores SIGTERM.
        command = ["timeout", "-k", "2", str(TIMEOUT_SECONDS), "python", f"/code/{script}"]

        try:
            output = client.containers.run(
                SANDBOX_IMAGE,
                command,
                volumes={tmp_dir: {"bind": "/code", "mode": "ro"}},
                network_disabled=True,
                mem_limit="128m",
                memswap_limit="128m",  # otherwise it gets another 128m of swap
                pids_limit=64,  # fork bombs
                remove=True,
            )
            return 0, output.decode("utf-8", errors="replace"), ""
        except docker.errors.ContainerError as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
            if e.exit_status == 124:
                stderr += f"\nTimed out after {TIMEOUT_SECONDS}s"
            elif e.exit_status == 137:
                stderr += "\nKilled (out of memory or ignored the timeout)"
            return e.exit_status, "", stderr  # docker only keeps stderr when the container fails
        finally:
            client.close()


def trim(text: str) -> str:
    # keep the end, that's where the traceback and final results are
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return "[output truncated]\n" + text[-MAX_OUTPUT_CHARS:]


def tester_node(state: PipelineState) -> dict:
    if state.test_code.strip():
        files = {CODE_FILE: state.code, TEST_FILE: state.test_code}
        returncode, stdout, stderr = run_in_sandbox(files, TEST_FILE)
    else:
        returncode, stdout, stderr = 1, "", "No test_code was provided, so nothing was tested."

    test_passed = returncode == 0

    return {
        "test_passed": test_passed,
        "test_results": [{"passed": test_passed, "returncode": returncode}],
        "stdout": trim(stdout),
        "stderr": trim(stderr),
        "status": "reviewing",
    }
