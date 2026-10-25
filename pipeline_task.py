import os
import time

from celery.signals import worker_init
from prometheus_client import start_http_server

from celery_app import celery_app
from graph import app as pipeline_app
from metrics import PIPELINE_DURATION, PIPELINE_ITERATIONS, PIPELINE_RUNS


# the agents run in the worker, not the API, so the worker needs its own
# /metrics endpoint. only works with --pool=solo, where tasks run in this process
@worker_init.connect
def start_metrics_server(**kwargs):
    start_http_server(int(os.getenv("WORKER_METRICS_PORT", "8001")))


@celery_app.task(name="run_pipeline_task")
def run_pipeline_task(task_description: str) -> dict:
    start = time.perf_counter()
    try:
        result = pipeline_app.invoke({"task_description": task_description})
    except Exception:
        PIPELINE_RUNS.labels("error").inc()
        raise
    PIPELINE_RUNS.labels(result["status"]).inc()
    PIPELINE_DURATION.observe(time.perf_counter() - start)
    PIPELINE_ITERATIONS.observe(result["iteration_count"])
    return result
