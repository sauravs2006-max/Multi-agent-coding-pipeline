from fastapi import FastAPI
from pydantic import BaseModel

from pipeline_task import run_pipeline_task
from celery_app import celery_app

api = FastAPI()


class TaskRequest(BaseModel):
    task_description: str


@api.post("/tasks")
def create_task(request: TaskRequest):
    async_result = run_pipeline_task.delay(request.task_description)
    return {"task_id": async_result.id, "status": "queued"}


@api.get("/tasks/{task_id}")
def get_task(task_id: str):
    async_result = celery_app.AsyncResult(task_id)

    if async_result.state == "PENDING":
        return {"task_id": task_id, "status": "running"}
    elif async_result.state == "SUCCESS":
        return {"task_id": task_id, "status": "done", "result": async_result.result}
    elif async_result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(async_result.result)}
    else:
        return {"task_id": task_id, "status": async_result.state}   