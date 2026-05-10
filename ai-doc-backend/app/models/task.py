from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentTask(Base):
    __tablename__ = "document_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    analyze_type: Mapped[str] = mapped_column(String(32), nullable=False)
    output_format: Mapped[str] = mapped_column(String(16), default="docx")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_ext: Mapped[str] = mapped_column(String(16), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    minio_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    error_code: Mapped[str] = mapped_column(String(64), default="")
    error_message: Mapped[str | None] = mapped_column(Text, default="")
    result_json: Mapped[dict | None] = mapped_column(JSON, default=None)
    report_minio_key: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
