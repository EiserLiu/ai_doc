import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()

    try:
        validate_file_size(len(content))
        file_ext = validate_file_extension(file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
