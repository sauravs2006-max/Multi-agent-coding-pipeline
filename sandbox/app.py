import logging
from contextlib import asynccontextmanager

import docker
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from . import runner

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sandbox")


@asynccontextmanager
async def lifespan(app):
    # pull the image at startup so the first real run isn't slow
    try:
        client = docker.from_env()
        runner.ensure_image(client)
        client.close()
    except (docker.errors.DockerException, requests.exceptions.ConnectionError) as e:
        log.warning("couldn't pull %s at startup: %s", runner.IMAGE, e)
    yield


app = FastAPI(lifespan=lifespan)


class RunRequest(BaseModel):
    # file names are fixed, so a file_name field (or anything unexpected) is a 422
    model_config = ConfigDict(extra="forbid")

    code: str = Field(max_length=100_000)
    tests: str = Field(max_length=100_000)
    timeout: int = Field(default=10, ge=1, le=30)


@app.post("/run")
def run(request: RunRequest):
    try:
        return runner.run(request.code, request.tests, request.timeout)
    except runner.DockerError as e:
        log.error("run failed: %s", e)
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/health")
def health():
    try:
        client = docker.from_env()
        client.ping()
        client.close()
    except (docker.errors.DockerException, requests.exceptions.ConnectionError):
        raise HTTPException(status_code=503, detail="docker unreachable")
    return {"status": "ok"}
