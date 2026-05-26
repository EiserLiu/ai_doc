import json
import logging
import threading

import pika

from app.config import settings

logger = logging.getLogger(__name__)

TASK_EXCHANGE = "doc.task.exchange"
TASK_QUEUE = "doc.task.queue"
TASK_ROUTING_KEY = "task.create"

RESULT_EXCHANGE = "doc.result.exchange"
RESULT_QUEUE = "doc.result.queue"
RESULT_ROUTING_KEY = "task.result"

LOG_EXCHANGE = "doc.log.exchange"
LOG_QUEUE = "doc.log.queue"
LOG_ROUTING_KEY = "task.log"

COST_EXCHANGE = "doc.cost.exchange"
COST_QUEUE = "doc.cost.queue"
COST_ROUTING_KEY = "task.cost"


def _get_connection():
    return pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))


def _setup_channel(channel):
    channel.exchange_declare(exchange=TASK_EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=TASK_QUEUE, durable=True)
    channel.queue_bind(TASK_QUEUE, TASK_EXCHANGE, routing_key=TASK_ROUTING_KEY)

    channel.exchange_declare(exchange=RESULT_EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=RESULT_QUEUE, durable=True)
    channel.queue_bind(RESULT_QUEUE, RESULT_EXCHANGE, routing_key=RESULT_ROUTING_KEY)

    channel.exchange_declare(exchange=LOG_EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=LOG_QUEUE, durable=True)
    channel.queue_bind(LOG_QUEUE, LOG_EXCHANGE, routing_key=LOG_ROUTING_KEY)

    channel.exchange_declare(exchange=COST_EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=COST_QUEUE, durable=True)
    channel.queue_bind(COST_QUEUE, COST_EXCHANGE, routing_key=COST_ROUTING_KEY)


def publish_task(task_message: dict):
    connection = _get_connection()
    try:
        channel = connection.channel()
        _setup_channel(channel)
        channel.basic_publish(
            exchange=TASK_EXCHANGE,
            routing_key=TASK_ROUTING_KEY,
            body=json.dumps(task_message, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        logger.info(f"Task published: {task_message.get('task_no')}")
    finally:
        connection.close()


def start_result_consumer(callback):
    """Start consuming result queue in a background thread."""

    def _consume():
        while True:
            try:
                connection = _get_connection()
                channel = connection.channel()
                _setup_channel(channel)
                channel.basic_consume(
                    queue=RESULT_QUEUE,
                    on_message_callback=callback,
                    auto_ack=True,
                )
                logger.info("Result consumer started")
                channel.start_consuming()
            except Exception as e:
                logger.error(f"Result consumer error: {e}, reconnecting in 5s...")
                import time
                time.sleep(5)

    thread = threading.Thread(target=_consume, daemon=True)
    thread.start()
    return thread


def start_log_consumer(callback):
    """Start consuming log queue in a background thread."""

    def _consume():
        while True:
            try:
                connection = _get_connection()
                channel = connection.channel()
                _setup_channel(channel)
                channel.basic_consume(
                    queue=LOG_QUEUE,
                    on_message_callback=callback,
                    auto_ack=True,
                )
                logger.info("Log consumer started")
                channel.start_consuming()
            except Exception as e:
                logger.error(f"Log consumer error: {e}, reconnecting in 5s...")
                import time
                time.sleep(5)

    thread = threading.Thread(target=_consume, daemon=True)
    thread.start()
    return thread


def start_cost_consumer(callback):
    """Start consuming cost queue in a background thread."""

    def _consume():
        while True:
            try:
                connection = _get_connection()
                channel = connection.channel()
                _setup_channel(channel)
                channel.basic_consume(
                    queue=COST_QUEUE,
                    on_message_callback=callback,
                    auto_ack=True,
                )
                logger.info("Cost consumer started")
                channel.start_consuming()
            except Exception as e:
                logger.error(f"Cost consumer error: {e}, reconnecting in 5s...")
                import time
                time.sleep(5)

    thread = threading.Thread(target=_consume, daemon=True)
    thread.start()
    return thread
