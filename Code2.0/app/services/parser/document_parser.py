import os
from typing import Any, Dict, List

from docx import Document

from app.services.parser.pdf_parser import PDFParser


class DocumentParser:
    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            parsed = PDFParser.parse_with_sections(file_path)
            return {
                "text": parsed["full_text"],
                "sections": parsed["sections"],
                "pages": parsed["pages"],
                "format": "pdf",
            }
        if ext == ".docx":
            return DocumentParser._parse_docx(file_path)
        if ext in {".txt", ".md", ".markdown"}:
            return DocumentParser._parse_text(file_path, ext)
        raise ValueError(f"Unsupported file type: {ext}")

    @staticmethod
    def _parse_docx(file_path: str) -> Dict[str, Any]:
        doc = Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
        sections: List[Dict[str, Any]] = []
        for idx, text in enumerate(paragraphs):
            if len(text) <= 80:
                sections.append({"title": text, "page_number": 1, "index": idx})
        return {
            "text": "\n".join(paragraphs),
            "sections": sections,
            "pages": [{"page_number": 1, "content": "\n".join(paragraphs)}],
            "format": "docx",
        }

    @staticmethod
    def _parse_text(file_path: str, ext: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        sections: List[Dict[str, Any]] = []
        for idx, line in enumerate(lines):
            if line.startswith("#") or (len(line) <= 80 and idx % 8 == 0):
                sections.append({"title": line[:150], "page_number": 1, "index": idx})
        return {
            "text": content,
            "sections": sections,
            "pages": [{"page_number": 1, "content": content}],
            "format": ext.lstrip("."),
        }
