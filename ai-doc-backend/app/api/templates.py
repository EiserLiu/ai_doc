import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.report_template import ReportTemplate
from app.schemas.template import TemplateResponse
from app.api.deps import get_current_user
from app.services import minio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.post("", response_model=TemplateResponse)
async def create_template(
    file: UploadFile = File(...),
    template_name: str = Form(..., min_length=1, max_length=128),
    analyze_type: str = Form(..., pattern="^(policy|bidding)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="仅支持 .docx 格式的模板文件")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit for templates
        raise HTTPException(status_code=400, detail="模板文件过大")

    minio_key = f"templates/{current_user.id}/{template_name}.docx"
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    minio_service.upload_file(minio_key, content, content_type)

    template = ReportTemplate(
        user_id=current_user.id,
        template_name=template_name,
        analyze_type=analyze_type,
        minio_key=minio_key,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("", response_model=list[TemplateResponse])
def list_templates(
    analyze_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ReportTemplate).filter(ReportTemplate.user_id == current_user.id)
    if analyze_type:
        query = query.filter(ReportTemplate.analyze_type == analyze_type)
    return query.order_by(ReportTemplate.created_at.desc()).all()


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id,
        ReportTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    try:
        minio_service.delete_file(template.minio_key)
    except Exception as e:
        logger.warning(f"Failed to delete template file from MinIO: {e}")

    db.delete(template)
    db.commit()
    return {"code": 0, "message": "success"}
