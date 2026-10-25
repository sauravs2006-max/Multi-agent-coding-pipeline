"""Each simulated user submits a task and polls until it finishes, like a real client."""
import random
import time

from locust import HttpUser, between, events, task

POLL_INTERVAL = 0.5
GIVE_UP_AFTER = 600  # seconds, so a stuck task counts as a failure instead of hanging the user

TASKS = [
    "Write a function add(a, b) that returns a + b.",
    "Write a function is_even(n) that returns True if n is even.",
    "Write a function reverse_words(s) that reverses the order of words in a sentence.",
]


def record(name, seconds, error=None):
    # shows up in the locust stats next to the real http requests, under type PIPELINE
    events.request.fire(request_type="PIPELINE", name=name, response_time=seconds * 1000,
                        response_length=0, exception=error, context={})


class PipelineUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def submit_and_wait(self):
        submitted = time.perf_counter()
        with self.client.post("/tasks", json={"task_description": random.choice(TASKS)},
                              name="POST /tasks", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"status {response.status_code}")
                return
            task_id = response.json()["task_id"]

        started = None
        while True:
            time.sleep(POLL_INTERVAL)
            with self.client.get(f"/tasks/{task_id}", name="GET /tasks/[id]", catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"status {response.status_code}")
                    return
                status = response.json()["status"]

            now = time.perf_counter()
            if status == "running" and started is None:
                started = now
                record("queue wait", started - submitted)
            if status in ("done", "failed", "error"):
                break
            if now - submitted > GIVE_UP_AFTER:
                record("end to end", now - submitted, error=TimeoutError("task never finished"))
                return

        if started is None:  # went from queued to finished between two polls
            started = now
        record("processing", now - started)
        error = RuntimeError("pipeline crashed") if status == "error" else None
        record("end to end", now - submitted, error=error)
