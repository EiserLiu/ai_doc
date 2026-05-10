from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotifyConfig(Base):
    __tablename__ = "notify_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    notify_type: Mapped[str] = mapped_column(String(32), nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_enabled: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=func.now())
