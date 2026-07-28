from celery_app import celery_app
from graph import app as pipeline_app


@celery_app.task(name="run_pipeline_task")
def run_pipeline_task(task_description: str) -> dict:
    result = pipeline_app.invoke({"task_description": task_description})
    return result