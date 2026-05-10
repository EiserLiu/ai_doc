import io
import logging

import fitz  # PyMuPDF
from docx import Document

logger = logging.getLogger(__name__)


def parse_file(file_bytes: bytes, file_ext: str) -> str:
    if file_ext == "pdf":
        return parse_pdf(file_bytes)
    elif file_ext == "docx":
        return parse_docx(file_bytes)
    else:
        raise ValueError(f"不支持的文件类型: .{file_ext}")


def parse_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    texts = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            texts.append(text.strip())
    doc.close()
    return "\n\n".join(texts)


def parse_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    texts = []

    for para in doc.paragraphs:
        if para.text.strip():
            texts.append(para.text.strip())

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                texts.append(" | ".join(cells))

    return "\n\n".join(texts)
