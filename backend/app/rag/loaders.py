"""文档文本抽取: 支持 md / txt / pdf / docx / xlsx"""
from pathlib import Path


def extract_text(file_path: str, file_type: str) -> str:
    """按文件类型抽取纯文本; Excel 表格转为"列名: 值"语义文本"""
    path = Path(file_path)

    if file_type in ("md", "txt"):
        return path.read_text(encoding="utf-8", errors="ignore")

    if file_type == "pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    if file_type == "docx":
        from docx import Document as DocxDocument

        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    if file_type == "xlsx":
        from openpyxl import load_workbook

        wb = load_workbook(path, read_only=True, data_only=True)
        parts = []
        for ws in wb.worksheets:
            rows = ws.iter_rows(values_only=True)
            header = next(rows, None)
            if header is None:
                continue
            lines = []
            for row in rows:
                pairs = [
                    f"{h}: {v}"
                    for h, v in zip(header, row)
                    if v is not None and str(v).strip()
                ]
                if pairs:
                    lines.append(" | ".join(pairs))
            if lines:
                parts.append(f"# 工作表 {ws.title}\n" + "\n".join(lines))
        return "\n\n".join(parts)

    raise ValueError(f"不支持的文件类型: {file_type}")
