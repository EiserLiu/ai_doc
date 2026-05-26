import logging
from pathlib import Path

from docxtpl import DocxTemplate

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

DISCLAIMER = (
    "免责声明：本报告由 AI 根据上传文件自动生成，仅用于辅助整理和初步分析。"
    "涉及法律、财务、投标、政策申报等重要事项，请以原文和专业人员审核为准。"
)


def generate(result: dict, analyze_type: str, output_format: str, task_no: str, template_minio_key: str = "") -> bytes:
    import io
    from app.services import minio_service
    from app.config import settings

    if template_minio_key:
        try:
            template_bytes = minio_service.download_file(settings.MINIO_BUCKET, template_minio_key)
            doc = DocxTemplate(io.BytesIO(template_bytes))
        except Exception as e:
            logger.warning(f"Failed to load custom template, falling back to default: {e}")
            template_path = TEMPLATES_DIR / f"{analyze_type}_report.docx"
            if not template_path.exists():
                raise FileNotFoundError(f"Report template not found: {template_path}")
            doc = DocxTemplate(template_path)
    else:
        template_path = TEMPLATES_DIR / f"{analyze_type}_report.docx"
        if not template_path.exists():
            raise FileNotFoundError(f"Report template not found: {template_path}")
        doc = DocxTemplate(template_path)

    context = dict(result)
    context["disclaimer"] = DISCLAIMER
    context["task_no"] = task_no

    doc.render(context)

    import io
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()
