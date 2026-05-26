import json
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import auth, tasks, notify, templates
from app.services import rabbitmq_service, task_service, notify_service, cache_service
from app.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_result_message(ch, method, properties, body):
    """Callback for consuming result messages from RabbitMQ."""
    try:
        message = json.loads(body)
        task_no = message["task_no"]
        status = message["status"]
        result_json = message.get("result_json")
        report_minio_key = message.get("report_minio_key", "")
        error_message = message.get("error_message", "")

        logger.info(f"Received result for task {task_no}: {status}")

        db = SessionLocal()
        try:
            kwargs = {}
            if result_json:
                kwargs["result_json"] = result_json
            if report_minio_key:
                kwargs["report_minio_key"] = report_minio_key
            if error_message:
                kwargs["error_message"] = error_message
                kwargs["error_code"] = "ALGORITHM_ERROR"

            task = task_service.update_task_status(db, task_no, status, **kwargs)
            cache_service.invalidate_task_cache(task_no)
            cache_service.invalidate_task_detail_cache(task_no)

            if task:
                from app.models.notify_config import NotifyConfig
                user_configs = db.query(NotifyConfig).filter(
                    NotifyConfig.user_id == task.user_id,
                    NotifyConfig.is_enabled == 1,
                ).all()

                for config in user_configs:
                    if status == "success" and result_json:
                        summary = result_json.get("summary", "") if isinstance(result_json, dict) else ""
                        title, content = notify_service.build_task_success_message(
                            task_no, task.original_filename, task.analyze_type, summary
                        )
                    else:
                        title, content = notify_service.build_task_failed_message(
                            task_no, task.original_filename, error_message
                        )
                    notify_service.send_notify(config.notify_type, config.webhook_url, title, content)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error processing result message: {e}")


def handle_log_message(ch, method, properties, body):
    """Callback for consuming log messages from RabbitMQ."""
    try:
        message = json.loads(body)
        task_no = message["task_no"]
        level = message.get("level", "INFO")
        log_message = message.get("message", "")

        db = SessionLocal()
        try:
            from app.models.task_log import TaskLog
            log_entry = TaskLog(task_no=task_no, level=level, message=log_message)
            db.add(log_entry)
            db.commit()
            logger.debug(f"Log saved for task {task_no}: [{level}] {log_message}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error processing log message: {e}")


def handle_cost_message(ch, method, properties, body):
    """Callback for consuming cost messages from RabbitMQ."""
    try:
        message = json.loads(body)
        task_no = message["task_no"]
        provider = message.get("provider", "")
        model = message.get("model", "")
        prompt_tokens = message.get("prompt_tokens", 0)
        completion_tokens = message.get("completion_tokens", 0)

        db = SessionLocal()
        try:
            from app.models.llm_call_log import LlmCallLog
            cost_entry = LlmCallLog(
                task_no=task_no,
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                success=1,
            )
            db.add(cost_entry)
            db.commit()
            logger.debug(f"Cost saved for task {task_no}: {prompt_tokens}+{completion_tokens} tokens")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error processing cost message: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()

    logger.info("Starting RabbitMQ result consumer...")
    rabbitmq_service.start_result_consumer(handle_result_message)

    logger.info("Starting RabbitMQ log consumer...")
    rabbitmq_service.start_log_consumer(handle_log_message)

    logger.info("Starting RabbitMQ cost consumer...")
    rabbitmq_service.start_cost_consumer(handle_cost_message)

    yield

    logger.info("Shutting down...")


app = FastAPI(
    title="AI 文档自动化助手 - 后端服务",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(notify.router)
app.include_router(templates.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "backend"}
