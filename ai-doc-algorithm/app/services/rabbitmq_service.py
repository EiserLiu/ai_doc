import json
import logging

import pika

from app.config import settings

logger = logging.getLogger(__name__)

RESULT_EXCHANGE = "doc.result.exchange"
RESULT_QUEUE = "doc.result.queue"
RESULT_ROUTING_KEY = "task.result"


def send_result(task_no: str, status: str, result_json: dict | None = None, report_minio_key: str = "", error_message: str = ""):
    message = {
        "task_no": task_no,
        "status": status,
        "result_json": result_json,
        "report_minio_key": report_minio_key,
        "error_message": error_message,
    }
    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=RESULT_EXCHANGE, exchange_type="direct", durable=True)
        channel.queue_declare(queue=RESULT_QUEUE, durable=True)
        channel.queue_bind(RESULT_QUEUE, RESULT_EXCHANGE, routing_key=RESULT_ROUTING_KEY)
        channel.basic_publish(
            exchange=RESULT_EXCHANGE,
            routing_key=RESULT_ROUTING_KEY,
            body=json.dumps(message, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        logger.info(f"Result sent for task {task_no}: {status}")
    finally:
        connection.close()
