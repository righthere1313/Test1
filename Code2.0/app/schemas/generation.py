from pydantic import BaseModel
from typing import List, Optional

# --- PPT Schemas ---

class BackgroundPart(BaseModel):
    image_path: str
    x: float
    y: float
    w: float
    h: float
    unit: Optional[str] = "emu"  # "emu" or "ratio"
    z: int = 0


class RectSpec(BaseModel):
    x: float
    y: float
    w: float
    h: float
    unit: Optional[str] = "emu"


class ChartSpec(BaseModel):
    id: str
    data: dict
    title: Optional[str] = None
    subtitle: Optional[str] = None
    position: Optional[str] = "right"
    policy: Optional[str] = "trim"


class SlideContent(BaseModel):
    title: str
    content: List[str]  # Bullet points or paragraphs
    content_blocks: Optional[List[List[str]]] = None
    notes: Optional[str] = None
    layout_index: int = 1  # 0=Title, 1=Title+Content, etc. (Standard PPT layouts)
    content_rect: Optional[RectSpec] = None
    background_image: Optional[str] = None
    background_keyword: Optional[str] = None
    background_parts: Optional[List[BackgroundPart]] = None
    image_path: Optional[str] = None
    image_keyword: Optional[str] = None
    image_filename: Optional[str] = None
    image_position: Optional[str] = "right"
    chart: Optional[ChartSpec] = None

class PPTPresentation(BaseModel):
    title: str
    subtitle: Optional[str] = None
    layout: Optional[str] = None
    cover_blocks: Optional[List[List[str]]] = None
    content_rect_default: Optional[RectSpec] = None
    slides: List[SlideContent]
    theme: Optional[str] = "default"
    template: Optional[str] = None
    background_image: Optional[str] = None
    background_keyword: Optional[str] = None
    background_parts_default: Optional[List[BackgroundPart]] = None
    image_position_default: Optional[str] = "right"

# --- DOCX Schemas ---

class DocxElement(BaseModel):
    type: str # "heading", "paragraph", "bullet", "numbered"
    content: str
    level: int = 1 # For headings (1-3)

class DocxDocument(BaseModel):
    title: str
    elements: List[DocxElement]
