from datetime import datetime

from sqlalchemy.orm import Session

from app.models.task import DocumentTask
from app.utils.file_utils import generate_task_no


def create_task(
    db: Session,
    user_id: int,
    analyze_type: str,
    output_format: str,
    original_filename: str,
    file_ext: str,
    file_size: int,
    minio_key: str,
) -> DocumentTask:
    task_no = generate_task_no()
    task = DocumentTask(
        task_no=task_no,
        user_id=user_id,
        analyze_type=analyze_type,
        output_format=output_format,
        original_filename=original_filename,
        file_ext=file_ext,
        file_size=file_size,
        minio_key=minio_key,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task_no: str, status: str, **kwargs):
    task = db.query(DocumentTask).filter(DocumentTask.task_no == task_no).first()
    if not task:
        return None
    task.status = status
    if status == "processing":
        task.started_at = datetime.now()
    elif status in ("success", "failed"):
        task.finished_at = datetime.now()
    for key, value in kwargs.items():
        if hasattr(task, key):
            setattr(task, key, value)
    db.commit()
    return task


def get_task(db: Session, task_no: str) -> DocumentTask | None:
    return db.query(DocumentTask).filter(DocumentTask.task_no == task_no).first()


def get_task_by_id(db: Session, task_id: int) -> DocumentTask | None:
    return db.query(DocumentTask).filter(DocumentTask.id == task_id).first()


def list_tasks(
    db: Session,
    user_id: int,
    status: str | None = None,
    analyze_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[DocumentTask], int]:
    query = db.query(DocumentTask).filter(DocumentTask.user_id == user_id)
    if status:
        query = query.filter(DocumentTask.status == status)
    if analyze_type:
        query = query.filter(DocumentTask.analyze_type == analyze_type)

    total = query.count()
    items = (
        query.order_by(DocumentTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def retry_task(db: Session, task_no: str) -> DocumentTask | None:
    task = get_task(db, task_no)
    if not task or task.status != "failed":
        return None
    task.status = "queued"
    task.error_code = ""
    task.error_message = ""
    task.started_at = None
    task.finished_at = None
    db.commit()
    db.refresh(task)
    return task
