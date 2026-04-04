import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.schemas.knowledge_base import DocumentInfo, DocumentVersionInfo, TemporaryUploadResponse, UploadResponse
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter()
kb_service = KnowledgeBaseService()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
SUPPORTED_EXTS = {".pdf", ".docx", ".txt", ".md", ".markdown"}


def _validate_file(file: UploadFile) -> tuple[str, str]:
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    return filename, ext


def _save_temp_upload(file: UploadFile, filename: str) -> str:
    temp_id = str(uuid.uuid4())
    return os.path.join(UPLOAD_DIR, f"{temp_id}_{filename}")


# @router.post("/upload", response_model=UploadResponse, status_code=201)
# async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
#     filename, ext = _validate_file(file)
#     temp_path = _save_temp_upload(file, filename)
#     try:
#         with open(temp_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#         result = kb_service.ingest_document(temp_path, filename, ext.lstrip("."))
#         return UploadResponse(
#             document_id=result["document_id"],
#             filename=filename,
#             file_type=ext.lstrip("."),
#             version=result["version"],
#             chunk_count=result["chunk_count"],
#             sections=result["sections"],
#             status="processed",
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)

@router.post("/upload/kb", response_model=UploadResponse, status_code=201)
async def upload_document_kb(file: UploadFile = File(...)) -> UploadResponse:
    filename, ext = _validate_file(file)
    temp_path = _save_temp_upload(file, filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        result = kb_service.ingest_document(temp_path, filename, ext.lstrip("."))
        return UploadResponse(
            document_id=result["document_id"],
            filename=filename,
            file_type=ext.lstrip("."),
            version=result["version"],
            chunk_count=result["chunk_count"],
            sections=result["sections"],
            status="processed",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/upload/staging", response_model=TemporaryUploadResponse, status_code=201)
async def upload_document_staging(
    file: UploadFile = File(...),
    session_id: str = Form(..., min_length=1),
    ttl_minutes: int = Form(default=120, ge=5, le=1440),
) -> TemporaryUploadResponse:
    filename, ext = _validate_file(file)
    temp_path = _save_temp_upload(file, filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        result = kb_service.stage_temporary_document(
            source_path=temp_path,
            filename=filename,
            file_type=ext.lstrip("."),
            session_id=session_id,
            ttl_minutes=ttl_minutes,
        )
        return TemporaryUploadResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/staging/documents", response_model=List[dict])
async def list_staging_documents(
    session_id: str | None = Query(default=None),
    include_expired: bool = Query(default=False),
) -> List[dict]:
    return kb_service.list_temporary_documents(session_id=session_id, include_expired=include_expired)


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents() -> List[DocumentInfo]:
    return [DocumentInfo(**item) for item in kb_service.list_documents()]


@router.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str) -> DocumentInfo:
    item = kb_service.get_document(document_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentInfo(**item)


@router.get("/documents/{document_id}/versions", response_model=List[DocumentVersionInfo])
async def list_document_versions(document_id: str) -> List[DocumentVersionInfo]:
    items = kb_service.list_document_versions(document_id)
    return [DocumentVersionInfo(**item) for item in items]


@router.get("/documents/{document_id}/versions/{version}/download")
async def download_document_version(document_id: str, version: int) -> FileResponse:
    versions = kb_service.list_document_versions(document_id)
    matched = next((item for item in versions if int(item["version"]) == version), None)
    if matched is None:
        raise HTTPException(status_code=404, detail="Version not found")
    file_path = matched["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    filename = os.path.basename(file_path)
    return FileResponse(path=file_path, filename=filename)


@router.delete("/documents/{document_id}", response_model=dict)
async def delete_document(document_id: str) -> dict:
    success = kb_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "document_id": document_id}
