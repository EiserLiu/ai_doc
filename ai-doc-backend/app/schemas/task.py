from datetime import datetime
from pydantic import BaseModel, Field


class TaskCreateResponse(BaseModel):
    task_no: str
    status: str = "pending"


class TaskDetail(BaseModel):
    task_no: str
    analyze_type: str
    output_format: str
    original_filename: str
    file_ext: str
    file_size: int
    status: str
    error_code: str = ""
    error_message: str = ""
    result_json: dict | None = None
    report_minio_key: str = ""
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskListItem(BaseModel):
    task_no: str
    original_filename: str
    analyze_type: str
    status: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    total: int
    items: list[TaskListItem]


class DownloadResponse(BaseModel):
    download_url: str
    filename: str
    expires_in: int = 3600
