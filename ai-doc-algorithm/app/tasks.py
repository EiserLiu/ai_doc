import logging

from app.celery_app import celery_app
from app.services import (
    minio_service,
    parser_service,
    text_service,
    llm_service,
    report_service,
    rabbitmq_service,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.analyze_document",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def analyze_document(self, task_message: dict):
    task_no = task_message["task_no"]
    analyze_type = task_message["analyze_type"]
    output_format = task_message["output_format"]
    minio_key = task_message["minio_key"]
    bucket = task_message["minio_bucket"]

    logger.info(f"Processing task {task_no}: type={analyze_type}, file={minio_key}")

    try:
        # 1. Download file from MinIO
        logger.info(f"[{task_no}] Downloading file from MinIO...")
        file_bytes = minio_service.download_file(bucket, minio_key)

        # 2. Parse text
        file_ext = minio_key.rsplit(".", 1)[-1].lower()
        logger.info(f"[{task_no}] Parsing {file_ext} file...")
        raw_text = parser_service.parse_file(file_bytes, file_ext)

        # 3. Clean text
        logger.info(f"[{task_no}] Cleaning text...")
        cleaned_text = text_service.clean_text(raw_text)

        if not cleaned_text.strip():
            raise ValueError("未提取到有效文本")

        # 4. Split + LLM analysis
        chunks = text_service.split_text(cleaned_text)
        logger.info(f"[{task_no}] Text split into {len(chunks)} chunks")

        if len(chunks) == 1:
            logger.info(f"[{task_no}] Analyzing single chunk...")
            result = llm_service.analyze(chunks[0], analyze_type)
        else:
            logger.info(f"[{task_no}] Analyzing {len(chunks)} chunks...")
            partials = []
            for i, chunk in enumerate(chunks):
                logger.info(f"[{task_no}] Analyzing chunk {i + 1}/{len(chunks)}...")
                partial = llm_service.analyze(chunk, analyze_type)
                partials.append(partial)
            logger.info(f"[{task_no}] Merging results...")
            result = llm_service.merge_results(partials, analyze_type)

        # 5. Generate report
        logger.info(f"[{task_no}] Generating report...")
        report_bytes = report_service.generate(result, analyze_type, output_format, task_no)
        report_key = f"reports/{task_no}_report.{output_format}"
        content_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if output_format == "docx"
            else "application/pdf"
        )
        minio_service.upload_file(bucket, report_key, report_bytes, content_type)

        # 6. Send success result
        logger.info(f"[{task_no}] Task completed successfully")
        rabbitmq_service.send_result(task_no, "success", result, report_key)

    except Exception as e:
        logger.error(f"[{task_no}] Task failed: {e}")
        rabbitmq_service.send_result(task_no, "failed", None, "", str(e))
