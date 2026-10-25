from .state import PipelineState
import os
import tempfile

import docker

SANDBOX_IMAGE = "python:3.11-slim"
TIMEOUT_SECONDS = 10


def tester_node(state: PipelineState) -> dict:
    # file_name comes from the LLM, so drop any "../" before writing it on the host
    file_name = os.path.basename(state.file_name) or "main.py"
    client = docker.from_env()

    with tempfile.TemporaryDirectory() as tmp_dir:
        with open(os.path.join(tmp_dir, file_name), "w", encoding="utf-8") as f:
            f.write(state.code)

        # run() with remove=True blocks with no timeout, so the limit is enforced
        # inside the container. -k sends SIGKILL if the code ignores SIGTERM.
        command = ["timeout", "-k", "2", str(TIMEOUT_SECONDS), "python", f"/code/{file_name}"]

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
            returncode = 0
            stdout = output.decode("utf-8", errors="replace")
            stderr = ""
        except docker.errors.ContainerError as e:
            returncode = e.exit_status
            stdout = ""  # docker only keeps stderr when the container fails
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
            if returncode == 124:
                stderr += f"\nTimed out after {TIMEOUT_SECONDS}s"
            elif returncode == 137:
                stderr += "\nKilled (out of memory or ignored the timeout)"
        finally:
            client.close()

    test_passed = returncode == 0

    return {
        "test_passed": test_passed,
        "test_results": [{"passed": test_passed, "returncode": returncode}],
        "stdout": stdout,
        "stderr": stderr,
        "status": "reviewing",
    }
