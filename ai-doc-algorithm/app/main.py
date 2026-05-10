import json
import logging
import threading
from contextlib import asynccontextmanager

import pika
from fastapi import FastAPI

from app.config import settings
from app.tasks import analyze_document

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TASK_EXCHANGE = "doc.task.exchange"
TASK_QUEUE = "doc.task.queue"
TASK_ROUTING_KEY = "task.create"


def _start_task_consumer():
    """Start consuming task queue in a background thread."""

    def _consume():
        while True:
            try:
                connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
                channel = connection.channel()

                channel.exchange_declare(exchange=TASK_EXCHANGE, exchange_type="direct", durable=True)
                channel.queue_declare(queue=TASK_QUEUE, durable=True)
                channel.queue_bind(TASK_QUEUE, TASK_EXCHANGE, routing_key=TASK_ROUTING_KEY)

                def _on_message(ch, method, properties, body):
                    try:
                        task_message = json.loads(body)
                        logger.info(f"Received task: {task_message.get('task_no')}")
                        # Process the task directly (synchronous)
                        analyze_document(task_message)
                        logger.info(f"Task completed: {task_message.get('task_no')}")
                    except Exception as e:
                        logger.error(f"Error processing task: {e}")

                channel.basic_consume(
                    queue=TASK_QUEUE,
                    on_message_callback=_on_message,
                    auto_ack=True,
                )
                logger.info("Task consumer started, waiting for messages...")
                channel.start_consuming()
            except Exception as e:
                logger.error(f"Task consumer error: {e}, reconnecting in 5s...")
                import time
                time.sleep(5)

    thread = threading.Thread(target=_consume, daemon=True)
    thread.start()
    return thread


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Algorithm service starting...")
    _start_task_consumer()
    yield
    logger.info("Algorithm service shutting down...")


app = FastAPI(
    title="AI 文档自动化助手 - 算法服务",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "algorithm"}
