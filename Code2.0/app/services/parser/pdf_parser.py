import logging
import re
from typing import Dict, List

import pdfplumber

logger = logging.getLogger(__name__)

class PDFParser:
    @staticmethod
    def parse_pdf(file_path: str) -> List[Dict[str, str]]:
        extracted_content = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        extracted_content.append({
                            "page_number": i + 1,
                            "content": text.strip()
                        })
            logger.info(f"Successfully parsed PDF: {file_path}, pages: {len(extracted_content)}")
            return extracted_content
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise e

    @staticmethod
    def extract_text_only(file_path: str) -> str:
        content_list = PDFParser.parse_pdf(file_path)
        return "\n\n".join([page["content"] for page in content_list])

    @staticmethod
    def parse_with_sections(file_path: str) -> Dict[str, object]:
        pages = PDFParser.parse_pdf(file_path)
        sections: List[Dict[str, object]] = []
        title_patterns = [
            r"^\s*第[一二三四五六七八九十百零\d]+[章节部分篇].*",
            r"^\s*\d+(\.\d+){0,2}\s+.+",
            r"^\s*[一二三四五六七八九十]+、.+",
            r"^\s*[（(]?[一二三四五六七八九十\d]+[）)]\s*.+",
        ]
        for page in pages:
            page_number = int(page["page_number"])
            for line in page["content"].splitlines():
                normalized = line.strip()
                if not normalized:
                    continue
                if any(re.match(pattern, normalized) for pattern in title_patterns):
                    sections.append({"title": normalized[:150], "page_number": page_number})
        return {
            "pages": pages,
            "sections": sections,
            "full_text": "\n\n".join([page["content"] for page in pages]),
        }
