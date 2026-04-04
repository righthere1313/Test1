import logging
from dotenv import load_dotenv
from pathlib import Path

from fastapi.staticfiles import StaticFiles
import os

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router

logging.basicConfig(level=logging.INFO)



    
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "TeachingAgent Local Knowledge Base Service",
        "docs_url": "/docs",
        "endpoints": {
            "upload_document": f"{settings.API_V1_STR}/files/upload",
            "list_documents": f"{settings.API_V1_STR}/files/documents",
            "fulltext_search": f"{settings.API_V1_STR}/chat/search/fulltext",
            "semantic_search": f"{settings.API_V1_STR}/chat/search/semantic",
            "hybrid_search": f"{settings.API_V1_STR}/chat/search/hybrid",
            "qa": f"{settings.API_V1_STR}/chat/qa"
        },
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
