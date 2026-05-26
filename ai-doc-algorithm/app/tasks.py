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
    template_minio_key = task_message.get("template_minio_key", "")

    logger.info(f"Processing task {task_no}: type={analyze_type}, file={minio_key}")
    rabbitmq_service.send_log(task_no, "INFO", f"开始处理任务: type={analyze_type}")

    try:
        # 1. Download file from MinIO
        logger.info(f"[{task_no}] Downloading file from MinIO...")
        rabbitmq_service.send_log(task_no, "INFO", "正在从 MinIO 下载文件...")
        file_bytes = minio_service.download_file(bucket, minio_key)

        # 2. Parse text
        file_ext = minio_key.rsplit(".", 1)[-1].lower()
        logger.info(f"[{task_no}] Parsing {file_ext} file...")
        rabbitmq_service.send_log(task_no, "INFO", f"正在解析 {file_ext} 文件...")
        raw_text = parser_service.parse_file(file_bytes, file_ext)

        # 3. Clean text
        logger.info(f"[{task_no}] Cleaning text...")
        rabbitmq_service.send_log(task_no, "INFO", "正在清洗文本...")
        cleaned_text = text_service.clean_text(raw_text)

        if not cleaned_text.strip():
            raise ValueError("未提取到有效文本")

        # 4. Split + LLM analysis
        chunks = text_service.split_text(cleaned_text)
        logger.info(f"[{task_no}] Text split into {len(chunks)} chunks")
        rabbitmq_service.send_log(task_no, "INFO", f"文本已分为 {len(chunks)} 个块，开始 AI 分析...")

        if len(chunks) == 1:
            logger.info(f"[{task_no}] Analyzing single chunk...")
            result = llm_service.analyze(chunks[0], analyze_type, task_no)
        else:
            logger.info(f"[{task_no}] Analyzing {len(chunks)} chunks...")
            partials = []
            for i, chunk in enumerate(chunks):
                logger.info(f"[{task_no}] Analyzing chunk {i + 1}/{len(chunks)}...")
                rabbitmq_service.send_log(task_no, "INFO", f"正在分析第 {i + 1}/{len(chunks)} 个文本块...")
                partial = llm_service.analyze(chunk, analyze_type, task_no)
                partials.append(partial)
            logger.info(f"[{task_no}] Merging results...")
            rabbitmq_service.send_log(task_no, "INFO", "正在合并分析结果...")
            result = llm_service.merge_results(partials, analyze_type, task_no)

        # 5. Generate report
        logger.info(f"[{task_no}] Generating report...")
        rabbitmq_service.send_log(task_no, "INFO", "正在生成报告...")
        report_bytes = report_service.generate(result, analyze_type, output_format, task_no, template_minio_key)
        report_key = f"reports/{task_no}_report.{output_format}"
        content_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if output_format == "docx"
            else "application/pdf"
        )
        minio_service.upload_file(bucket, report_key, report_bytes, content_type)

        # 6. Send success result
        logger.info(f"[{task_no}] Task completed successfully")
        rabbitmq_service.send_log(task_no, "INFO", "任务处理完成")
        rabbitmq_service.send_result(task_no, "success", result, report_key)

    except Exception as e:
        logger.error(f"[{task_no}] Task failed: {e}")
        rabbitmq_service.send_log(task_no, "ERROR", f"任务处理失败: {e}")
        rabbitmq_service.send_result(task_no, "failed", None, "", str(e))
