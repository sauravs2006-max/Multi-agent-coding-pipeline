import time

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


def run(script, timeout=tester.TIMEOUT_SECONDS):
    return tester.run_in_sandbox(code="", tests=script, timeout=timeout)


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
def test_failing_assert_keeps_stdout():
    state = PipelineState(task_description="t", code="def add(a, b):\n    return a - b",
                          test_code="from solution import add\nprint('checking add')\nassert add(2, 3) == 5")
    result = tester.tester_node(state)
    assert not result["test_passed"]
    assert "AssertionError" in result["stderr"]
    assert "checking add" in result["stdout"]  # lost with the old ContainerError version


def test_missing_tests_fail_without_running():
    result = tester.tester_node(PipelineState(task_description="t", code="x = 1", test_code="  "))
    assert not result["test_passed"]
    assert "No test_code" in result["stderr"]


@needs_docker
def test_infinite_loop_times_out():
    result = run("while True: pass", timeout=2)
    assert result["exit_code"] == 124
    assert result["timed_out"]
    assert "Timed out" in result["stderr"]


@needs_docker
def test_ignoring_sigterm_gets_killed():
    script = "import signal\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\nwhile True: pass"
    result = run(script, timeout=2)
    assert result["exit_code"] == 137
    assert result["timed_out"]
    assert not result["oom_killed"]


@needs_docker
def test_no_network():
    result = run("import socket\nsocket.create_connection(('8.8.8.8', 53), timeout=3)")
    assert result["exit_code"] != 0
    assert "Network is unreachable" in result["stderr"]


@needs_docker
def test_memory_limit_is_reported_as_oom():
    result = run("x = bytearray(500 * 1024 * 1024)")
    assert result["exit_code"] == 137
    assert result["oom_killed"]
    assert not result["timed_out"]
    assert "out of memory" in result["stderr"]


@needs_docker
def test_fork_bomb_is_capped():
    script = (
        "import os, time\n"
        "for _ in range(500):\n"
        "    if os.fork() == 0:\n"
        "        time.sleep(30)\n"
        "        os._exit(0)\n"
    )
    result = run(script)
    assert result["exit_code"] != 0
    assert "Resource temporarily unavailable" in result["stderr"]


@needs_docker
def test_mount_is_read_only():
    result = run("open('/code/hacked.txt', 'w').write('x')")
    assert result["exit_code"] != 0
    assert "Read-only file system" in result["stderr"]


@needs_docker
def test_runs_as_nobody():
    result = run("import os\nprint(os.getuid())")
    assert result["stdout"].strip() == "65534"


@needs_docker
def test_printing_forever_is_capped_and_stops_on_time():
    start = time.monotonic()
    result = run("i = 0\nwhile True:\n    print(i)\n    i += 1", timeout=3)
    took = time.monotonic() - start
    assert result["timed_out"]
    assert result["stdout"].startswith("[output truncated]")
    assert len(result["stdout"]) < tester.MAX_OUTPUT_CHARS + 100
    assert took < 3 + 6  # the old version spent 8 more seconds pulling the output


def test_docker_down_raises_sandbox_error(monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "tcp://127.0.0.1:1")  # nothing listens here
    with pytest.raises(tester.SandboxError, match="Docker Desktop"):
        run("print('hi')")
