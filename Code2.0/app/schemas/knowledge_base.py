from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentVersionInfo(BaseModel):
    version: int
    file_path: str
    content_hash: str
    created_at: datetime


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    file_type: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    version: int
    chunk_count: int
    sections: List[Dict[str, Any]]
    status: str


class TemporaryUploadResponse(BaseModel):
    temp_document_id: str
    session_id: str
    filename: str
    file_type: str
    status: str
    expires_at: datetime
    chunk_count: int
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: Optional[str] = None


class SearchHit(BaseModel):
    chunk_id: str
    score: float
    content: str
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    mode: str
    query: str
    results: List[SearchHit]


class AnswerRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: Optional[str] = None
    temporary_document_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    intent: Optional[str] = None
    task_payload: Optional[Dict[str, Any]] = None


class AnswerResponse(BaseModel):
    query: str
    answer: str
    citations: List[Dict[str, Any]]
    intent: Optional[str] = None
    intent_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    intent_reason: Optional[str] = None
    intent_source: Optional[str] = None
    route: Optional[str] = None
    task_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class IntentDetectRequest(BaseModel):
    query: str = Field(min_length=1)


class IntentDetectResponse(BaseModel):
    query: str
    intent: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    source: str
    error: Optional[str] = None
