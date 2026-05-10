import os
from datetime import datetime

from app.config import settings


def validate_file_extension(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.allowed_extensions_list:
        raise ValueError(f"不支持的文件类型: .{ext}，仅支持: {settings.ALLOWED_EXTENSIONS}")
    return ext


def validate_file_size(size: int):
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise ValueError(f"文件大小超过限制: {size / 1024 / 1024:.1f}MB，最大 {settings.MAX_UPLOAD_SIZE_MB}MB")
    if size == 0:
        raise ValueError("不允许上传空文件")


def generate_task_no() -> str:
    now = datetime.now()
    date_str = now.strftime("%Y%m%d%H%M%S")
    import random
    seq = random.randint(1000, 9999)
    return f"TASK{date_str}{seq}"


def build_minio_key(task_no: str, filename: str, category: str = "uploads") -> str:
    now = datetime.now()
    date_path = now.strftime("%Y/%m/%d")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return f"{category}/{date_path}/{task_no}_original.{ext}"
