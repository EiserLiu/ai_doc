from celery import Celery
from kombu import Queue, Exchange
from app.config import settings

celery_app = Celery(
    "doc_algorithm",
    broker=settings.RABBITMQ_URL,
    backend=f"{settings.REDIS_URL}/1",
)

task_exchange = Exchange("doc.task.exchange", type="direct")

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_queue="doc.task.queue",
    task_queues=(
        Queue("doc.task.queue", task_exchange, routing_key="task.create"),
    ),
    task_routes={
        "app.tasks.analyze_document": {"queue": "doc.task.queue"},
    },
)

celery_app.autodiscover_tasks(["app"])
