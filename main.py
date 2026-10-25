from fastapi import FastAPI, HTTPException
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
    state = async_result.state

    if state == "PENDING":
        raise HTTPException(status_code=404, detail="task not found")
    elif state == "SENT":
        return {"task_id": task_id, "status": "queued"}
    elif state == "STARTED":
        return {"task_id": task_id, "status": "running"}
    elif state == "SUCCESS":
        # the task finished, but the pipeline itself can still end as "failed"
        result = async_result.result
        return {"task_id": task_id, "status": result["status"], "result": result}
    elif state == "FAILURE":
        # crashed (gemini or docker down), different from the pipeline giving up
        return {"task_id": task_id, "status": "error", "error": str(async_result.result)}
    else:
        return {"task_id": task_id, "status": state}
