import pytest
from fastapi.testclient import TestClient

from sandbox.app import app
from test_sandbox import needs_docker

client = TestClient(app)


def test_file_name_is_rejected():
    # the old tester took file_name from the LLM, which allowed "../" paths on the host
    response = client.post("/run", json={"code": "x = 1", "tests": "pass", "file_name": "../../evil.py"})
    assert response.status_code == 422


@pytest.mark.parametrize("timeout", [0, 31])
def test_timeout_is_bounded(timeout):
    response = client.post("/run", json={"code": "", "tests": "pass", "timeout": timeout})
    assert response.status_code == 422


def test_docker_down_is_a_503(monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "tcp://127.0.0.1:1")
    response = client.post("/run", json={"code": "", "tests": "print('hi')"})
    assert response.status_code == 503
    assert "docker" in response.json()["detail"]
    assert client.get("/health").status_code == 503


@needs_docker
def test_run_returns_the_result():
    response = client.post("/run", json={"code": "", "tests": "print('hi')\nraise SystemExit(2)", "timeout": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["exit_code"] == 2
    assert body["stdout"].strip() == "hi"
    assert body["timed_out"] is False
    assert client.get("/health").json() == {"status": "ok"}
