from celery import Celery
from celery.signals import before_task_publish

celery_app = Celery(
    "pipeline_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["pipeline_task"],
)
celery_app.conf.task_track_started = True


# Celery reports PENDING for queued tasks and for ids it has never seen, so save
# a SENT state before publishing. Anything still PENDING was never submitted.
# before_ (not after_) so a fast worker can't write STARTED first and get overwritten.
@before_task_publish.connect
def mark_as_sent(headers=None, **kwargs):
    celery_app.backend.store_result(headers["id"], None, "SENT")
