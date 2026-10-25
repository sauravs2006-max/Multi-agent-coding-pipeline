# shared by the api and the worker, compose picks the command
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ agents/
COPY celery_app.py graph.py main.py metrics.py pipeline_task.py ./

# neither the api nor the worker needs root, and celery complains when it has it
RUN useradd --create-home app
USER app

CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "8000"]
