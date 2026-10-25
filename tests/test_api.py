from types import SimpleNamespace

from fastapi.testclient import TestClient

import main

client = TestClient(main.api)


def fake_task(monkeypatch, state, result=None):
    monkeypatch.setattr(main.celery_app, "AsyncResult", lambda task_id: SimpleNamespace(state=state, result=result))


class FakeRedis:
    def __init__(self, up):
        self.up = up

    def ping(self):
        if not self.up:
            raise main.redis.exceptions.ConnectionError("down")
        return True


def test_health(monkeypatch):
    # celery keeps one backend object per thread, so patch the class, not the instance
    backend_class = type(main.celery_app.backend)
    monkeypatch.setattr(backend_class, "client", property(lambda self: FakeRedis(up=True)))
    assert client.get("/health").json() == {"status": "ok"}
    monkeypatch.setattr(backend_class, "client", property(lambda self: FakeRedis(up=False)))
    assert client.get("/health").status_code == 503


def test_unknown_task_is_404(monkeypatch):
    fake_task(monkeypatch, "PENDING")
    assert client.get("/tasks/made-up-id").status_code == 404


def test_queued_and_running(monkeypatch):
    fake_task(monkeypatch, "SENT")
    assert client.get("/tasks/abc").json()["status"] == "queued"
    fake_task(monkeypatch, "STARTED")
    assert client.get("/tasks/abc").json()["status"] == "running"


def test_status_comes_from_the_pipeline(monkeypatch):
    fake_task(monkeypatch, "SUCCESS", {"status": "failed", "approved": False})
    body = client.get("/tasks/abc").json()
    assert body["status"] == "failed"
    assert body["result"]["approved"] is False


def test_crash_is_reported_as_error(monkeypatch):
    fake_task(monkeypatch, "FAILURE", RuntimeError("can't reach docker"))
    body = client.get("/tasks/abc").json()
    assert body["status"] == "error"
    assert "docker" in body["error"]
