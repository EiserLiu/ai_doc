import json
import logging

import pika

from app.config import settings

logger = logging.getLogger(__name__)

RESULT_EXCHANGE = "doc.result.exchange"
RESULT_QUEUE = "doc.result.queue"
RESULT_ROUTING_KEY = "task.result"

LOG_EXCHANGE = "doc.log.exchange"
LOG_QUEUE = "doc.log.queue"
LOG_ROUTING_KEY = "task.log"

COST_EXCHANGE = "doc.cost.exchange"
COST_QUEUE = "doc.cost.queue"
COST_ROUTING_KEY = "task.cost"


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


def send_log(task_no: str, level: str, message: str):
    log_msg = {"task_no": task_no, "level": level, "message": message}
    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=LOG_EXCHANGE, exchange_type="direct", durable=True)
        channel.queue_declare(queue=LOG_QUEUE, durable=True)
        channel.queue_bind(LOG_QUEUE, LOG_EXCHANGE, routing_key=LOG_ROUTING_KEY)
        channel.basic_publish(
            exchange=LOG_EXCHANGE,
            routing_key=LOG_ROUTING_KEY,
            body=json.dumps(log_msg, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    finally:
        connection.close()


def send_cost_log(task_no: str, provider: str, model: str, prompt_tokens: int, completion_tokens: int):
    cost_msg = {
        "task_no": task_no,
        "provider": provider,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=COST_EXCHANGE, exchange_type="direct", durable=True)
        channel.queue_declare(queue=COST_QUEUE, durable=True)
        channel.queue_bind(COST_QUEUE, COST_EXCHANGE, routing_key=COST_ROUTING_KEY)
        channel.basic_publish(
            exchange=COST_EXCHANGE,
            routing_key=COST_ROUTING_KEY,
            body=json.dumps(cost_msg, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    finally:
        connection.close()
