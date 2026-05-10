from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.notify_config import NotifyConfig
from app.schemas.notify import (
    NotifyConfigCreate,
    NotifyConfigUpdate,
    NotifyConfigResponse,
    NotifyTestRequest,
)
from app.api.deps import get_current_user
from app.services.notify_service import send_notify

router = APIRouter(prefix="/api/notify-config", tags=["notify"])


@router.post("", response_model=NotifyConfigResponse)
def create_notify_config(
    req: NotifyConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(NotifyConfig)
        .filter(
            NotifyConfig.user_id == current_user.id,
            NotifyConfig.notify_type == req.notify_type,
        )
        .first()
    )
    if existing:
        existing.webhook_url = req.webhook_url
        existing.is_enabled = 1 if req.is_enabled else 0
        db.commit()
        db.refresh(existing)
        return existing

    config = NotifyConfig(
        user_id=current_user.id,
        notify_type=req.notify_type,
        webhook_url=req.webhook_url,
        is_enabled=1 if req.is_enabled else 0,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("", response_model=list[NotifyConfigResponse])
def list_notify_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    configs = db.query(NotifyConfig).filter(NotifyConfig.user_id == current_user.id).all()
    return configs


@router.put("/{config_id}", response_model=NotifyConfigResponse)
def update_notify_config(
    config_id: int,
    req: NotifyConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = db.query(NotifyConfig).filter(
        NotifyConfig.id == config_id,
        NotifyConfig.user_id == current_user.id,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="通知配置不存在")
    if req.webhook_url is not None:
        config.webhook_url = req.webhook_url
    if req.is_enabled is not None:
        config.is_enabled = 1 if req.is_enabled else 0
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}")
def delete_notify_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = db.query(NotifyConfig).filter(
        NotifyConfig.id == config_id,
        NotifyConfig.user_id == current_user.id,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="通知配置不存在")
    db.delete(config)
    db.commit()
    return {"code": 0, "message": "success"}


@router.post("/test")
def test_notify(
    req: NotifyTestRequest,
    current_user: User = Depends(get_current_user),
):
    success = send_notify(
        req.notify_type,
        req.webhook_url,
        "AI 文档助手 - 测试通知",
        "这是一条测试通知，说明 Webhook 配置正确。",
    )
    if success:
        return {"code": 0, "message": "通知发送成功"}
    raise HTTPException(status_code=500, detail="通知发送失败")
