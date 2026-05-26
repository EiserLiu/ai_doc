import io
import json
import logging
import zipfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.task import (
    TaskCreateResponse,
    TaskDetail,
    TaskListItem,
    TaskListResponse,
    DownloadResponse,
    BatchTaskResult,
)
from app.api.deps import get_current_user
from app.utils.file_utils import validate_file_extension, validate_file_size, build_minio_key
from app.services import minio_service, task_service, rabbitmq_service, cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskCreateResponse)
async def create_task(
    file: UploadFile = File(...),
    analyze_type: str = Form(..., pattern="^(policy|bidding)$"),
    output_format: str = Form(default="docx", pattern="^(docx|pdf)$"),
    template_id: int | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()

    try:
        validate_file_size(len(content))
        file_ext = validate_file_extension(file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Look up template minio_key if template_id provided
    template_minio_key = ""
    if template_id:
        from app.models.report_template import ReportTemplate
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id,
            ReportTemplate.user_id == current_user.id,
        ).first()
        if template:
            template_minio_key = template.minio_key

    task = task_service.create_task(
        db=db,
        user_id=current_user.id,
        analyze_type=analyze_type,
        output_format=output_format,
        original_filename=file.filename or "unknown",
        file_ext=file_ext,
        file_size=len(content),
        minio_key="",
    )

    minio_key = build_minio_key(task.task_no, file.filename or "unknown.pdf")
    content_type = file.content_type or "application/octet-stream"
    minio_service.upload_file(minio_key, content, content_type)

    task.minio_key = minio_key
    db.commit()

    task_message = {
        "task_no": task.task_no,
        "analyze_type": analyze_type,
        "output_format": output_format,
        "original_filename": file.filename or "unknown",
        "minio_bucket": settings.MINIO_BUCKET,
        "minio_key": minio_key,
        "template_minio_key": template_minio_key,
    }
    try:
        rabbitmq_service.publish_task(task_message)
        task_service.update_task_status(db, task.task_no, "queued")
    except Exception as e:
        logger.error(f"Failed to publish task to RabbitMQ: {e}")
        task_service.update_task_status(
            db, task.task_no, "failed",
            error_code="QUEUE_ERROR",
            error_message=f"任务队列发送失败: {e}",
        )
        raise HTTPException(status_code=500, detail="任务队列发送失败")

    cache_service.cache_task_status(task.task_no, "queued")

    return TaskCreateResponse(task_no=task.task_no, status="queued")


@router.post("/batch", response_model=list[BatchTaskResult])
async def create_tasks_batch(
    files: list[UploadFile] = File(...),
    analyze_type: str = Form(..., pattern="^(policy|bidding)$"),
    output_format: str = Form(default="docx", pattern="^(docx|pdf)$"),
    template_id: int | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Look up template minio_key if template_id provided
    template_minio_key = ""
    if template_id:
        from app.models.report_template import ReportTemplate
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id,
            ReportTemplate.user_id == current_user.id,
        ).first()
        if template:
            template_minio_key = template.minio_key

    results = []
    for file in files:
        try:
            content = await file.read()
            validate_file_size(len(content))
            file_ext = validate_file_extension(file.filename or "")

            task = task_service.create_task(
                db=db,
                user_id=current_user.id,
                analyze_type=analyze_type,
                output_format=output_format,
                original_filename=file.filename or "unknown",
                file_ext=file_ext,
                file_size=len(content),
                minio_key="",
            )

            minio_key = build_minio_key(task.task_no, file.filename or "unknown.pdf")
            content_type = file.content_type or "application/octet-stream"
            minio_service.upload_file(minio_key, content, content_type)

            task.minio_key = minio_key
            db.commit()

            task_message = {
                "task_no": task.task_no,
                "analyze_type": analyze_type,
                "output_format": output_format,
                "original_filename": file.filename or "unknown",
                "minio_bucket": settings.MINIO_BUCKET,
                "minio_key": minio_key,
                "template_minio_key": template_minio_key,
            }
            try:
                rabbitmq_service.publish_task(task_message)
                task_service.update_task_status(db, task.task_no, "queued")
            except Exception as e:
                logger.error(f"Failed to publish task to RabbitMQ: {e}")
                task_service.update_task_status(
                    db, task.task_no, "failed",
                    error_code="QUEUE_ERROR",
                    error_message=f"任务队列发送失败: {e}",
                )

            cache_service.cache_task_status(task.task_no, "queued")
            results.append(BatchTaskResult(task_no=task.task_no, status="queued", filename=file.filename or ""))
        except ValueError as e:
            results.append(BatchTaskResult(filename=file.filename or "", error=str(e)))
        except Exception as e:
            logger.error(f"Batch upload error for {file.filename}: {e}")
            results.append(BatchTaskResult(filename=file.filename or "", error=str(e)))

    return results


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: str | None = Query(default=None),
    analyze_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = task_service.list_tasks(
        db, current_user.id, status, analyze_type, page, page_size
    )
    return TaskListResponse(total=total, items=items)


@router.get("/{task_no}", response_model=TaskDetail)
def get_task_detail(
    task_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cached = cache_service.get_task_detail_cache(task_no)
    if cached and cached.get("user_id") == current_user.id:
        return TaskDetail(**cached)

    task = task_service.get_task(db, task_no)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该任务")
    return task


@router.get("/{task_no}/result")
def get_task_result(
    task_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = task_service.get_task(db, task_no)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该任务")
    if task.status != "success":
        raise HTTPException(status_code=400, detail=f"任务状态为 {task.status}，无法获取结果")
    if not task.result_json:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    return {"code": 0, "message": "success", "data": task.result_json}


@router.get("/{task_no}/download", response_model=DownloadResponse)
def download_report(
    task_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = task_service.get_task(db, task_no)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该任务")
    if task.status != "success":
        raise HTTPException(status_code=400, detail="任务未完成，无法下载")
    if not task.report_minio_key:
        raise HTTPException(status_code=404, detail="报告文件不存在")

    url = minio_service.get_presigned_url(task.report_minio_key, expires=3600)
    filename = f"{task.task_no}_report.{task.output_format}"
    return DownloadResponse(download_url=url, filename=filename)


@router.post("/download-batch")
def download_batch(
    task_nos: list[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.task import DocumentTask
    tasks = db.query(DocumentTask).filter(
        DocumentTask.task_no.in_(task_nos),
        DocumentTask.user_id == current_user.id,
        DocumentTask.status == "success",
        DocumentTask.report_minio_key != "",
    ).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="无可用报告")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for task in tasks:
            try:
                file_bytes = minio_service.download_file(task.report_minio_key)
                base_name = task.original_filename.rsplit(".", 1)[0] if "." in task.original_filename else task.original_filename
                arcname = f"{base_name}_report.{task.output_format}"
                zf.writestr(arcname, file_bytes)
            except Exception as e:
                logger.error(f"Failed to download report for task {task.task_no}: {e}")
    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=reports_batch.zip"},
    )


@router.post("/{task_no}/retry", response_model=TaskCreateResponse)
def retry_task(
    task_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = task_service.get_task(db, task_no)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作该任务")
    if task.status != "failed":
        raise HTTPException(status_code=400, detail="仅失败任务可重试")

    updated = task_service.retry_task(db, task_no)
    if not updated:
        raise HTTPException(status_code=500, detail="重试失败")

    task_message = {
        "task_no": task.task_no,
        "analyze_type": task.analyze_type,
        "output_format": task.output_format,
        "original_filename": task.original_filename,
        "minio_bucket": settings.MINIO_BUCKET,
        "minio_key": task.minio_key,
    }
    try:
        rabbitmq_service.publish_task(task_message)
    except Exception as e:
        logger.error(f"Failed to publish retry task to RabbitMQ: {e}")
        task_service.update_task_status(
            db, task.task_no, "failed",
            error_code="QUEUE_ERROR",
            error_message=f"任务队列发送失败: {e}",
        )
        raise HTTPException(status_code=500, detail="任务队列发送失败")

    cache_service.cache_task_status(task_no, "queued")
    return TaskCreateResponse(task_no=task.task_no, status="queued")


@router.get("/{task_no}/logs")
def get_task_logs(
    task_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = task_service.get_task(db, task_no)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该任务")

    from app.models.task_log import TaskLog
    logs = db.query(TaskLog).filter(TaskLog.task_no == task_no).order_by(TaskLog.created_at.asc()).all()
    return [
        {"level": l.level, "message": l.message, "created_at": l.created_at.isoformat() if l.created_at else ""}
        for l in logs
    ]


@router.get("/stats/llm-cost")
def get_llm_cost_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.llm_call_log import LlmCallLog
    from app.models.task import DocumentTask
    from sqlalchemy import func

    # Get cost stats for the user's tasks
    stats = (
        db.query(
            LlmCallLog.model,
            func.count(LlmCallLog.id).label("call_count"),
            func.sum(LlmCallLog.prompt_tokens).label("total_prompt_tokens"),
            func.sum(LlmCallLog.completion_tokens).label("total_completion_tokens"),
        )
        .join(DocumentTask, DocumentTask.task_no == LlmCallLog.task_no)
        .filter(DocumentTask.user_id == current_user.id)
        .group_by(LlmCallLog.model)
        .all()
    )

    total_calls = sum(s.call_count for s in stats)
    total_prompt = sum(s.total_prompt_tokens or 0 for s in stats)
    total_completion = sum(s.total_completion_tokens or 0 for s in stats)

    return {
        "total_calls": total_calls,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_prompt + total_completion,
        "by_model": [
            {
                "model": s.model,
                "call_count": s.call_count,
                "prompt_tokens": s.total_prompt_tokens or 0,
                "completion_tokens": s.total_completion_tokens or 0,
            }
            for s in stats
        ],
    }
