from fastapi import APIRouter

from app.api.v1.endpoints import chat, files, generate, templates, user

api_router = APIRouter()
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(generate.router, prefix="/generate", tags=["generate"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
