import docker
import pytest

from agents import tester
from agents.state import PipelineState


def docker_available():
    try:
        docker.from_env().close()
        return True
    except docker.errors.DockerException:
        return False


needs_docker = pytest.mark.skipif(not docker_available(), reason="docker isn't running")


def run(code):
    return tester.run_in_sandbox({"main.py": code}, "main.py")


@needs_docker
def test_tests_import_the_solution():
    state = PipelineState(
        task_description="t",
        code="def add(a, b):\n    return a + b",
        test_code="from solution import add\nassert add(2, 3) == 5\nprint('ok')",
    )
    result = tester.tester_node(state)
    assert result["test_passed"]
    assert result["stdout"].strip() == "ok"


@needs_docker
def test_failing_assert():
    state = PipelineState(task_description="t", code="def add(a, b):\n    return a - b",
                          test_code="from solution import add\nassert add(2, 3) == 5")
    result = tester.tester_node(state)
    assert not result["test_passed"]
    assert "AssertionError" in result["stderr"]


def test_missing_tests_fail_without_running():
    result = tester.tester_node(PipelineState(task_description="t", code="x = 1", test_code="  "))
    assert not result["test_passed"]
    assert "No test_code" in result["stderr"]


@needs_docker
def test_infinite_loop_times_out(monkeypatch):
    monkeypatch.setattr(tester, "TIMEOUT_SECONDS", 2)
    returncode, _, stderr = run("while True: pass")
    assert returncode == 124
    assert "Timed out" in stderr


@needs_docker
def test_ignoring_sigterm_gets_killed(monkeypatch):
    monkeypatch.setattr(tester, "TIMEOUT_SECONDS", 2)
    code = "import signal\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\nwhile True: pass"
    assert run(code)[0] == 137


@needs_docker
def test_no_network():
    returncode, _, stderr = run("import socket\nsocket.create_connection(('8.8.8.8', 53), timeout=3)")
    assert returncode != 0
    assert "Network is unreachable" in stderr


@needs_docker
def test_memory_limit():
    assert run("x = bytearray(500 * 1024 * 1024)")[0] == 137


@needs_docker
def test_fork_bomb_is_capped():
    code = (
        "import os, time\n"
        "for _ in range(500):\n"
        "    if os.fork() == 0:\n"
        "        time.sleep(30)\n"
        "        os._exit(0)\n"
    )
    returncode, _, stderr = run(code)
    assert returncode != 0
    assert "Resource temporarily unavailable" in stderr


@needs_docker
def test_mount_is_read_only():
    returncode, _, stderr = run("open('/code/hacked.txt', 'w').write('x')")
    assert returncode != 0
    assert "Read-only file system" in stderr


@needs_docker
def test_long_output_is_trimmed():
    state = PipelineState(task_description="t", code="", test_code="print('x' * 100_000)\nprint('end')")
    stdout = tester.tester_node(state)["stdout"]
    assert stdout.startswith("[output truncated]")
    assert stdout.rstrip().endswith("end")
    assert len(stdout) < tester.MAX_OUTPUT_CHARS + 100


def test_docker_down_raises_sandbox_error(monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "tcp://127.0.0.1:1")  # nothing listens here
    with pytest.raises(tester.SandboxError, match="Docker Desktop"):
        run("print('hi')")
