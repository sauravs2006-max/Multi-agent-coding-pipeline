import io
import tarfile

import docker
import requests
from docker.types import LogConfig

IMAGE = "python:3.11-slim"
CODE_FILE = "solution.py"
TEST_FILE = "test_solution.py"
MAX_OUTPUT_CHARS = 4000

# docker keeps at most 1 MB of logs per container, so "print forever" can't fill memory
LOG_CONFIG = LogConfig(type=LogConfig.types.JSON, config={"max-size": "1m", "max-file": "1"})
LABELS = {"app": "pipeline-sandbox"}  # makes leftovers easy to find if the service crashes mid-run


class DockerError(Exception):
    pass


def trim(text):
    # keep the end, that's where the traceback and final results are
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return "[output truncated]\n" + text[-MAX_OUTPUT_CHARS:]


def ensure_image(client):
    try:
        client.images.get(IMAGE)
    except docker.errors.ImageNotFound:
        client.images.pull(IMAGE)


def _tar(files):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o444
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _copy_into_volume(client, volume_name, files):
    # this service runs in a container itself, so bind mounting its own temp dir
    # would point at a path that doesn't exist on the docker host. the files go into
    # a volume instead, through a container that is never started
    loader = client.containers.create(IMAGE, volumes={volume_name: {"bind": "/code", "mode": "rw"}},
                                      network_disabled=True, labels=LABELS)
    try:
        loader.put_archive("/code", _tar(files))
    finally:
        loader.remove(force=True)


def _execute(client, volume_name, timeout):
    # SIGTERM at the timeout, SIGKILL 2s later if the code ignores it
    command = ["timeout", "-k", "2", str(timeout), "python", f"/code/{TEST_FILE}"]
    container = client.containers.run(
        IMAGE,
        command,
        volumes={volume_name: {"bind": "/code", "mode": "ro"}},
        network_disabled=True,
        mem_limit="128m",
        memswap_limit="128m",  # otherwise it gets another 128m of swap
        pids_limit=64,  # fork bombs
        user="nobody",
        cap_drop=["ALL"],
        security_opt=["no-new-privileges"],
        log_config=LOG_CONFIG,
        labels=LABELS,
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
    return exit_code, oom_killed, stdout, stderr


def run(code, tests, timeout=10):
    """Run the tests against the code in a throwaway container."""
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        raise DockerError("can't reach docker, is it running?") from e

    try:
        ensure_image(client)
        volume = client.volumes.create(labels=LABELS)
        try:
            _copy_into_volume(client, volume.name, {CODE_FILE: code, TEST_FILE: tests})
            exit_code, oom_killed, stdout, stderr = _execute(client, volume.name, timeout)
        finally:
            volume.remove(force=True)
    except (docker.errors.DockerException, requests.exceptions.ConnectionError) as e:
        # docker went away mid-run, or the image couldn't be pulled
        raise DockerError(f"docker error: {e}") from e
    finally:
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
