FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY sandbox/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sandbox/ sandbox/

# stays root: it needs the docker socket, which is the trade-off explained in the README
CMD ["uvicorn", "sandbox.app:app", "--host", "0.0.0.0", "--port", "8080"]
