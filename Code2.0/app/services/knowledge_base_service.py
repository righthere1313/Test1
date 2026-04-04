import hashlib
import json
import logging
import math
import os
import re
import shutil
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, List, Optional, Sequence

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.parser.document_parser import DocumentParser

logger = logging.getLogger(__name__)


class LocalHashEmbeddings:
    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimensions
        for token in text.split():
            index = abs(hash(token)) % self.dimensions
            vector[index] += 1.0
        norm = sum(x * x for x in vector) ** 0.5
        if norm == 0:
            return vector
        return [x / norm for x in vector]


class KnowledgeBaseService:
    _instance: Optional["KnowledgeBaseService"] = None
    _lock = Lock()

    def __new__(cls) -> "KnowledgeBaseService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        os.makedirs(settings.RAW_STORAGE_DIR, exist_ok=True)
        os.makedirs(settings.PROCESSED_STORAGE_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(settings.METADATA_DB_PATH), exist_ok=True)
        os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
        self.temp_raw_dir = os.path.join(settings.RAW_STORAGE_DIR, "_staging")
        self.temp_processed_dir = os.path.join(settings.PROCESSED_STORAGE_DIR, "_staging")
        os.makedirs(self.temp_raw_dir, exist_ok=True)
        os.makedirs(self.temp_processed_dir, exist_ok=True)
        self.sqlite = sqlite3.connect(
            settings.METADATA_DB_PATH,
            check_same_thread=False,
            timeout=5.0,
        )
        self.sqlite.row_factory = sqlite3.Row # 支持列名索引和位置索引
        try:
            self.sqlite.execute("PRAGMA journal_mode=WAL;")
            self.sqlite.execute("PRAGMA synchronous=NORMAL;")
            self.sqlite.execute("PRAGMA busy_timeout=5000;")
        except Exception:
            pass
        self._init_tables()
        self.embeddings = self._build_embeddings()
        
        # 初始化 Chroma（支持本地和服务器两种模式
        if settings.CHROMA_USE_SERVER:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_SERVER_HOST,
                port=settings.CHROMA_SERVER_PORT,
                settings=ChromaSettings(
                    anonymized_telemetry=False
                )
            )
            self.vector_store = Chroma(
                collection_name=settings.COLLECTION_NAME,
                client=chroma_client,
                embedding_function=self.embeddings,
            )
        else:
            self.vector_store = Chroma(
                collection_name=settings.COLLECTION_NAME,
                persist_directory=settings.CHROMA_DB_DIR,
                embedding_function=self.embeddings,
            )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        self.reranker = self._build_reranker()
        self.llm = self._build_llm()
        self.max_parallel_workers = 2
        self.vector_enabled = True

    def _build_embeddings(self) -> Any:
        if settings.USE_LOCAL_EMBEDDING:
            return LocalHashEmbeddings()
        try:
            embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
            embeddings.embed_query("health check")
            return embeddings
        except Exception:
            logger.warning("Fallback to LocalHashEmbeddings because external model is unavailable")
            return LocalHashEmbeddings()

    def _build_reranker(self) -> Optional[Any]:
        model_name = (os.getenv("RERANKER_MODEL_NAME") or getattr(settings, "RERANKER_MODEL_NAME", "") or "").strip()
        if not model_name:
            return None
        try:
            from sentence_transformers import CrossEncoder
            return CrossEncoder(model_name)
        except Exception:
            logger.warning("CrossEncoder initialization failed", exc_info=True)
            return None

    def _build_llm(self) -> Optional[Any]:
        api_key = (os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "") or "").strip()
        model_name = (os.getenv("OPENAI_MODEL") or getattr(settings, "OPENAI_MODEL", "") or "").strip()
        base_url = (os.getenv("OPENAI_BASE_URL") or getattr(settings, "OPENAI_BASE_URL", "") or "").strip()
        dash_key = (os.getenv("DASHSCOPE_API_KEY") or getattr(settings, "DASHSCOPE_API_KEY", "") or "").strip()
        try:
            from langchain_openai import ChatOpenAI
            effective_api_key = api_key or (dash_key if base_url else "")
            if effective_api_key and model_name and (base_url or "gpt" in model_name or "o1" in model_name):
                kwargs: Dict[str, Any] = {"model": model_name, "api_key": effective_api_key, "temperature": 0.2}
                if base_url:
                    kwargs["base_url"] = base_url
                import httpx

                kwargs["http_client"] = httpx.Client(timeout=60, trust_env=False)
                kwargs["http_async_client"] = httpx.AsyncClient(timeout=60, trust_env=False)
                return ChatOpenAI(**kwargs)
        except Exception:
            logger.warning("ChatOpenAI initialization failed", exc_info=True)
        try:
            if dash_key:
                from langchain_community.chat_models.tongyi import ChatTongyi
                qwen_model = model_name or "qwen-turbo"
                return ChatTongyi(model=qwen_model, api_key=dash_key)
        except Exception:
            logger.warning("ChatTongyi initialization failed (ensure `pip install dashscope`)", exc_info=True)
        return None

    def _init_tables(self) -> None:
        cursor = self.sqlite.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                current_version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_versions (
                version_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                parsed_path TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                keywords TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS temporary_documents (
                temp_document_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                file_path TEXT NOT NULL,
                parsed_path TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS temporary_chunks (
                chunk_id TEXT PRIMARY KEY,
                temp_document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                keywords TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversation_messages_session_created_at ON conversation_messages (session_id, created_at)"
        )
        self.sqlite.commit()

    def ingest_document(self, source_path: str, filename: str, file_type: str) -> Dict[str, Any]:
        try:
            now = datetime.now(timezone.utc).isoformat()
            content_hash = self._sha256(source_path)
            document_row = self._find_document(filename)
            if document_row:
                document_id = document_row["document_id"]
                version = int(document_row["current_version"]) + 1
                self._update_document_version(document_id, version, now)
            else:
                document_id = str(uuid.uuid4())
                version = 1
                self._create_document(document_id, filename, file_type, now)
            raw_file_path = self._store_raw_file(source_path, document_id, version, filename)
            parsed = DocumentParser.parse(raw_file_path)
            parsed_path = self._store_parsed_json(parsed, document_id, version)
            version_id = str(uuid.uuid4())
            self._create_document_version(
                version_id=version_id,
                document_id=document_id,
                version=version,
                file_path=raw_file_path,
                parsed_path=parsed_path,
                content_hash=content_hash,
                created_at=now,
            )
            chunks = self._build_chunks(parsed["text"], document_id, version, filename, source="knowledge_base")
            self._replace_chunks(document_id=document_id, version=version, chunks=chunks)
            logger.info("Ingested knowledge-base document %s v%s", document_id, version)
            return {
                "document_id": document_id,
                "version": version,
                "chunk_count": len(chunks),
                "sections": parsed["sections"],
                "file_path": raw_file_path,
            }
        except Exception:
            logger.exception("Failed to ingest document: %s", filename)
            raise

    def stage_temporary_document(
        self,
        source_path: str,
        filename: str,
        file_type: str,
        session_id: str,
        ttl_minutes: int = 120,
    ) -> Dict[str, Any]:
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        expires_at = (now_dt + timedelta(minutes=max(ttl_minutes, 5))).isoformat()
        temp_document_id = str(uuid.uuid4())
        status = "staged"
        content_hash = self._sha256(source_path)
        file_path = ""
        parsed_path = ""
        try:
            file_path = self._store_temp_raw_file(source_path, temp_document_id, filename)
            parsed = DocumentParser.parse(file_path)
            parsed_path = self._store_temp_parsed_json(parsed, temp_document_id)
            metadata = self._extract_temp_metadata(parsed, file_path, filename, session_id)
            self._create_temporary_document(
                temp_document_id=temp_document_id,
                session_id=session_id,
                filename=filename,
                file_type=file_type,
                status=status,
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
                file_path=file_path,
                parsed_path=parsed_path,
                content_hash=content_hash,
                metadata=metadata,
            )
            chunks = self._build_chunks(
                parsed["text"],
                document_id=temp_document_id,
                version=1,
                filename=filename,
                source="temporary",
                extra_metadata={"session_id": session_id, "temp_document_id": temp_document_id},
            )
            self._replace_temporary_chunks(temp_document_id=temp_document_id, chunks=chunks)
            self._update_temporary_status(temp_document_id, "indexed")
            logger.info("Staged temporary document %s for session %s", temp_document_id, session_id)
            return {
                "temp_document_id": temp_document_id,
                "session_id": session_id,
                "filename": filename,
                "file_type": file_type,
                "status": "indexed",
                "expires_at": expires_at,
                "chunk_count": len(chunks),
                "sections": parsed["sections"],
                "metadata": metadata,
            }
        except Exception:
            logger.exception("Failed to stage temporary document: %s", filename)
            if temp_document_id:
                self._update_temporary_status(temp_document_id, "failed")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if parsed_path and os.path.exists(parsed_path):
                os.remove(parsed_path)
            raise

    def list_documents(self) -> List[Dict[str, Any]]:
        cursor = self.sqlite.cursor()
        rows = cursor.execute(
            "SELECT document_id, filename, file_type, current_version, created_at, updated_at FROM documents ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]

    def list_temporary_documents(self, session_id: Optional[str] = None, include_expired: bool = False) -> List[Dict[str, Any]]:
        self.cleanup_expired_temporary_documents()
        cursor = self.sqlite.cursor()
        conditions: List[str] = []
        params: List[Any] = []
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        if not include_expired:
            conditions.append("status != 'expired'")
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        rows = cursor.execute(
            f"""
            SELECT temp_document_id, session_id, filename, file_type, status, created_at, updated_at, expires_at, metadata_json
            FROM temporary_documents
            {where_clause}
            ORDER BY updated_at DESC
            """,
            tuple(params),
        ).fetchall()
        items: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json"))
            items.append(item)
        return items

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.sqlite.cursor()
        row = cursor.execute(
            "SELECT document_id, filename, file_type, current_version, created_at, updated_at FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_temporary_document(self, temp_document_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.sqlite.cursor()
        row = cursor.execute(
            """
            SELECT temp_document_id, session_id, filename, file_type, status, created_at, updated_at, expires_at, metadata_json
            FROM temporary_documents
            WHERE temp_document_id = ?
            """,
            (temp_document_id,),
        ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json"))
        return item

    def list_document_versions(self, document_id: str) -> List[Dict[str, Any]]:
        cursor = self.sqlite.cursor()
        rows = cursor.execute(
            """
            SELECT version, file_path, content_hash, created_at
            FROM document_versions
            WHERE document_id = ?
            ORDER BY version DESC
            """,
            (document_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def fulltext_search(self, query: str, top_k: int, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cursor = self.sqlite.cursor()
        terms = self._query_terms(query)
        like_query = f"%{query}%"
        where_conditions: List[str] = []
        params: List[Any] = []
        if document_id:
            where_conditions.append("document_id = ?")
            params.append(document_id)
        text_conditions = ["content LIKE ?"]
        text_params: List[Any] = [like_query]
        for term in terms:
            like_term = f"%{term}%"
            text_conditions.append("content LIKE ?")
            text_conditions.append("keywords LIKE ?")
            text_params.extend([like_term, like_term])
        where_conditions.append("(" + " OR ".join(text_conditions) + ")")
        params.extend(text_params)
        rows = cursor.execute(
            f"""
            SELECT chunk_id, content, metadata_json
            FROM chunks
            WHERE {' AND '.join(where_conditions)}
            LIMIT ?
            """,
            tuple(params + [max(top_k * 10, 30)]),
        ).fetchall()
        scored = []
        for row in rows:
            content = row["content"]
            score = self._keyword_overlap_score(query, content, terms)
            if score <= 0:
                continue
            scored.append(
                {
                    "chunk_id": row["chunk_id"],
                    "score": score,
                    "content": content,
                    "metadata": json.loads(row["metadata_json"]),
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def semantic_search(self, query: str, top_k: int, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.vector_enabled:
            return self.fulltext_search(query, top_k, document_id)
        search_kwargs: Dict[str, Any] = {"k": top_k}
        if document_id:
            search_kwargs["filter"] = {"document_id": document_id}
        try:
            docs_and_scores = self.vector_store.similarity_search_with_score(query, **search_kwargs)
        except Exception:
            logger.exception("Vector semantic search failed, fallback to fulltext search")
            self.vector_enabled = False
            return self.fulltext_search(query, top_k, document_id)
        results: List[Dict[str, Any]] = []
        for doc, score in docs_and_scores:
            normalized = 1.0 / (1.0 + float(score))
            results.append(
                {
                    "chunk_id": str(doc.metadata.get("chunk_id", "")),
                    "score": normalized,
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
            )
        return [item for item in results if item["metadata"].get("source") != "temporary"]

    def hybrid_search(self, query: str, top_k: int, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        semantic = self.semantic_search(query, max(top_k, 5), document_id)
        fulltext = self.fulltext_search(query, max(top_k, 5), document_id)
        return self._merge_search_results(semantic, fulltext, top_k)

    def temporary_fulltext_search(
        self,
        query: str,
        top_k: int,
        temporary_document_ids: Optional[Sequence[str]] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        self.cleanup_expired_temporary_documents()
        cursor = self.sqlite.cursor()
        terms = self._query_terms(query)
        like_query = f"%{query}%"
        where_conditions = ["td.status = 'indexed'"]
        params: List[Any] = []
        text_conditions = ["tc.content LIKE ?"]
        text_params: List[Any] = [like_query]
        for term in terms:
            like_term = f"%{term}%"
            text_conditions.append("tc.content LIKE ?")
            text_conditions.append("tc.keywords LIKE ?")
            text_params.extend([like_term, like_term])
        where_conditions.append("(" + " OR ".join(text_conditions) + ")")
        params.extend(text_params)
        if session_id:
            where_conditions.append("td.session_id = ?")
            params.append(session_id)
        rows = cursor.execute(
            f"""
            SELECT tc.chunk_id, tc.content, tc.metadata_json
            FROM temporary_chunks tc
            JOIN temporary_documents td ON td.temp_document_id = tc.temp_document_id
            WHERE {' AND '.join(where_conditions)}
            LIMIT ?
            """,
            tuple(params + [max(top_k * 5, 10)]),
        ).fetchall()
        id_set = set(temporary_document_ids or [])
        scored: List[Dict[str, Any]] = []
        for row in rows:
            metadata = json.loads(row["metadata_json"])
            if id_set and metadata.get("temp_document_id") not in id_set:
                continue
            content = row["content"]
            score = self._keyword_overlap_score(query, content, terms)
            if score <= 0:
                continue
            scored.append(
                {
                    "chunk_id": row["chunk_id"],
                    "score": score,
                    "content": content,
                    "metadata": metadata,
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def temporary_semantic_search(
        self,
        query: str,
        top_k: int,
        temporary_document_ids: Optional[Sequence[str]] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        self.cleanup_expired_temporary_documents()
        if not self.vector_enabled:
            return self.temporary_fulltext_search(query, top_k, temporary_document_ids, session_id)
        search_kwargs: Dict[str, Any] = {"k": max(top_k * 5, 10), "filter": {"source": "temporary"}}
        try:
            docs_and_scores = self.vector_store.similarity_search_with_score(query, **search_kwargs)
        except Exception:
            logger.exception("Temporary vector semantic search failed, fallback to fulltext search")
            self.vector_enabled = False
            return self.temporary_fulltext_search(query, top_k, temporary_document_ids, session_id)
        id_set = set(temporary_document_ids or [])
        results: List[Dict[str, Any]] = []
        for doc, score in docs_and_scores:
            metadata = dict(doc.metadata)
            if metadata.get("source") != "temporary":
                continue
            if session_id and metadata.get("session_id") != session_id:
                continue
            if id_set and metadata.get("temp_document_id") not in id_set:
                continue
            normalized = 1.0 / (1.0 + float(score))
            results.append(
                {
                    "chunk_id": str(metadata.get("chunk_id", "")),
                    "score": normalized,
                    "content": doc.page_content,
                    "metadata": metadata,
                }
            )
            if len(results) >= top_k:
                break
        return results

    def temporary_hybrid_search(
        self,
        query: str,
        top_k: int,
        temporary_document_ids: Optional[Sequence[str]] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        semantic = self.temporary_semantic_search(query, max(top_k, 5), temporary_document_ids, session_id)
        fulltext = self.temporary_fulltext_search(query, max(top_k, 5), temporary_document_ids, session_id)
        return self._merge_search_results(semantic, fulltext, top_k)

    def answer(
        self,
        query: str,
        top_k: int,
        document_id: Optional[str] = None,
        temporary_document_ids: Optional[Sequence[str]] = None,
        session_id: Optional[str] = None,
        require_llm: bool = False,
    ) -> Dict[str, Any]:
        self.cleanup_expired_temporary_documents()
        with ThreadPoolExecutor(max_workers=self.max_parallel_workers) as pool:
            kb_future = pool.submit(self.hybrid_search, query, max(top_k * 2, 8), document_id)
            temp_future = pool.submit(
                self.temporary_hybrid_search,
                query,
                max(top_k * 2, 8),
                temporary_document_ids,
                session_id,
            )
            kb_results = kb_future.result()
            temp_results = temp_future.result()
        candidates = kb_results + temp_results
        results = self._smart_rerank(query, candidates, top_k)
        if not results:
            if require_llm:
                raise RuntimeError("LLM is required but no retrieval context was found")
            fallback_results = self._fallback_recent_chunks(top_k, document_id, temporary_document_ids, session_id)
            if fallback_results:
                answer = self._generate_answer(query, fallback_results, session_id=session_id, require_llm=require_llm)
                self._remember_session_turn(session_id, query, answer)
                citations = []
                for item in fallback_results:
                    metadata = dict(item["metadata"])
                    citations.append(
                        {
                            "document_id": metadata.get("document_id"),
                            "filename": metadata.get("filename"),
                            "version": metadata.get("version"),
                            "chunk_id": metadata.get("chunk_id"),
                            "chunk_index": metadata.get("chunk_index"),
                            "score": item["score"],
                            "source": metadata.get("source", "knowledge_base"),
                            "session_id": metadata.get("session_id"),
                            "temp_document_id": metadata.get("temp_document_id"),
                        }
                    )
                return {"query": query, "answer": answer, "citations": citations}
            self._remember_session_turn(session_id, query, "未检索到相关内容，请尝试更具体的问题或先上传文档。")
            return {
                "query": query,
                "answer": "未检索到相关内容，请尝试更具体的问题或先上传文档。",
                "citations": [],
            }
        answer = self._generate_answer(query, results, session_id=session_id, require_llm=require_llm)
        self._remember_session_turn(session_id, query, answer)
        citations = []
        for item in results:
            metadata = dict(item["metadata"])
            citations.append(
                {
                    "document_id": metadata.get("document_id"),
                    "filename": metadata.get("filename"),
                    "version": metadata.get("version"),
                    "chunk_id": metadata.get("chunk_id"),
                    "chunk_index": metadata.get("chunk_index"),
                    "score": item["score"],
                    "source": metadata.get("source", "knowledge_base"),
                    "session_id": metadata.get("session_id"),
                    "temp_document_id": metadata.get("temp_document_id"),
                }
            )
        return {"query": query, "answer": answer, "citations": citations}

    def _remember_session_turn(self, session_id: Optional[str], query: str, answer: str) -> None:
        if not session_id:
            return
        try:
            self._add_session_message(session_id, "user", query)
            self._add_session_message(session_id, "assistant", answer)
            self._trim_session_messages(session_id, max_messages=20)
        except Exception:
            logger.warning("Session memory update failed for session %s", session_id, exc_info=True)

    def _add_session_message(self, session_id: str, role: str, content: str) -> None:
        text = str(content or "").strip()
        if not session_id or role not in {"user", "assistant"} or not text:
            return
        cursor = self.sqlite.cursor()
        cursor.execute(
            """
            INSERT INTO conversation_messages (message_id, session_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), session_id, role, text[:4000], datetime.now(timezone.utc).isoformat()),
        )
        self.sqlite.commit()

    def _trim_session_messages(self, session_id: str, max_messages: int = 20) -> None:
        limit = max(4, int(max_messages))
        cursor = self.sqlite.cursor()
        rows = cursor.execute(
            """
            SELECT message_id
            FROM conversation_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            """,
            (session_id,),
        ).fetchall()
        if len(rows) <= limit:
            return
        remove_ids = [row["message_id"] for row in rows[limit:]]
        cursor.executemany("DELETE FROM conversation_messages WHERE message_id = ?", [(item,) for item in remove_ids])
        self.sqlite.commit()

    def _get_session_messages(self, session_id: Optional[str], limit: int = 6) -> List[Dict[str, str]]:
        if not session_id:
            return []
        cap = max(2, int(limit))
        cursor = self.sqlite.cursor()
        rows = cursor.execute(
            """
            SELECT role, content
            FROM conversation_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (session_id, cap),
        ).fetchall()
        items = [{"role": str(row["role"]), "content": str(row["content"])} for row in rows]
        items.reverse()
        return items

    def _suggest_missing_info(self, query: str, history: List[Dict[str, str]]) -> Optional[str]:
        text = (query or "").strip()
        lowered = text.lower()
        if not text:
            return "请先告诉我你的具体问题或任务目标，例如课程主题、文档类型或期望输出。"

        short_ambiguous = {"怎么做", "怎么写", "帮我弄一下", "做一下", "优化一下", "改一下"}
        if text in short_ambiguous or len(text) <= 4:
            return "当前信息较少。请补充任务目标、使用场景和期望输出格式，我再给你更准确的结果。"

        has_reference_words = any(token in text for token in ["这个", "这个文档", "这份", "上面的", "刚才那个", "它"])
        if has_reference_words and not history:
            return "你提到了“这份/这个”内容，但当前会话没有可引用的历史信息。请补充具体对象（文档名、页码或段落）。"

        has_ppt = any(token in lowered for token in ["ppt", "幻灯片", "课件", "演示文稿"])
        if has_ppt:
            generic_ppt = re.fullmatch(r".*(生成|做|制作|创建).*(ppt|幻灯片|课件).*", lowered) is not None
            if generic_ppt and len(text) <= 24:
                return "为了生成更准确的PPT，请补充：1) 主题 2) 受众年级/学段 3) 页数范围 4) 风格偏好。"

        has_word = any(token in lowered for token in ["word", "docx", "文档", "报告", "论文", "说明书"])
        if has_word:
            generic_word = re.fullmatch(r".*(生成|写|创建|起草).*(word|docx|文档|报告).*", lowered) is not None
            if generic_word and len(text) <= 24:
                return "为了生成更准确的Word文档，请补充：1) 主题 2) 用途 3) 目标字数或篇幅 4) 结构要求。"

        return None

    def _render_history_for_prompt(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "无"
        lines: List[str] = []
        for item in history[-6:]:
            role = "用户" if item.get("role") == "user" else "助手"
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            lines.append(f"- {role}: {content[:280]}")
        return "\n".join(lines) if lines else "无"

    def cleanup_expired_temporary_documents(self) -> int:
        cursor = self.sqlite.cursor()
        now = datetime.now(timezone.utc).isoformat()
        rows = cursor.execute(
            """
            SELECT temp_document_id, file_path, parsed_path
            FROM temporary_documents
            WHERE expires_at <= ? AND status != 'expired'
            """,
            (now,),
        ).fetchall()
        if not rows:
            return 0
        cleaned = 0
        for row in rows:
            temp_document_id = row["temp_document_id"]
            chunk_rows = cursor.execute(
                "SELECT chunk_id FROM temporary_chunks WHERE temp_document_id = ?",
                (temp_document_id,),
            ).fetchall()
            chunk_ids = [item["chunk_id"] for item in chunk_rows]
            cursor.execute("DELETE FROM temporary_chunks WHERE temp_document_id = ?", (temp_document_id,))
            cursor.execute(
                "UPDATE temporary_documents SET status = 'expired', updated_at = ? WHERE temp_document_id = ?",
                (now, temp_document_id),
            )
            self.sqlite.commit()
            if chunk_ids and self.vector_enabled:
                try:
                    self.vector_store.delete(ids=chunk_ids)
                except Exception:
                    logger.exception("Vector cleanup failed for temp document %s, disable vector search", temp_document_id)
                    self.vector_enabled = False
            file_path = row["file_path"]
            parsed_path = row["parsed_path"]
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if parsed_path and os.path.exists(parsed_path):
                os.remove(parsed_path)
            raw_dir = os.path.dirname(file_path) if file_path else ""
            if raw_dir and os.path.isdir(raw_dir):
                try:
                    raw_dir_abs = os.path.abspath(raw_dir)
                    raw_base_abs = os.path.abspath(self.temp_raw_dir)
                    if (
                        os.path.commonpath([raw_dir_abs, raw_base_abs]) == raw_base_abs
                        and not os.listdir(raw_dir_abs)
                    ):
                        os.rmdir(raw_dir_abs)
                except Exception:
                    logger.debug("Skip removing raw temp directory: %s", raw_dir, exc_info=True)
            parsed_dir = os.path.dirname(parsed_path) if parsed_path else ""
            if parsed_dir and os.path.isdir(parsed_dir):
                try:
                    parsed_dir_abs = os.path.abspath(parsed_dir)
                    parsed_base_abs = os.path.abspath(self.temp_processed_dir)
                    if (
                        os.path.commonpath([parsed_dir_abs, parsed_base_abs]) == parsed_base_abs
                        and not os.listdir(parsed_dir_abs)
                    ):
                        os.rmdir(parsed_dir_abs)
                except Exception:
                    logger.debug("Skip removing parsed temp directory: %s", parsed_dir, exc_info=True)
            cleaned += 1
        if cleaned:
            logger.info("Cleaned %s expired temporary documents", cleaned)
        return cleaned

    def delete_document(self, document_id: str) -> bool:
        cursor = self.sqlite.cursor()
        doc_row = cursor.execute(
            "SELECT document_id FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()
        if not doc_row:
            return False
        
        version_rows = cursor.execute(
            "SELECT file_path, parsed_path FROM document_versions WHERE document_id = ?",
            (document_id,),
        ).fetchall()
        
        chunk_rows = cursor.execute(
            "SELECT chunk_id FROM chunks WHERE document_id = ?",
            (document_id,),
        ).fetchall()
        chunk_ids = [item["chunk_id"] for item in chunk_rows]
        
        cursor.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        cursor.execute("DELETE FROM document_versions WHERE document_id = ?", (document_id,))
        cursor.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        self.sqlite.commit()
        
        if chunk_ids and self.vector_enabled:
            try:
                self.vector_store.delete(ids=chunk_ids)
            except Exception:
                logger.exception("Vector cleanup failed for document %s, disable vector search", document_id)
                self.vector_enabled = False
        
        for row in version_rows:
            file_path = row["file_path"]
            parsed_path = row["parsed_path"]
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if parsed_path and os.path.exists(parsed_path):
                os.remove(parsed_path)
        
        logger.info("Deleted document %s", document_id)
        return True

    def _find_document(self, filename: str) -> Optional[sqlite3.Row]:
        cursor = self.sqlite.cursor()
        return cursor.execute(
            "SELECT document_id, current_version FROM documents WHERE filename = ?",
            (filename,),
        ).fetchone()

    def _create_document(self, document_id: str, filename: str, file_type: str, now: str) -> None:
        cursor = self.sqlite.cursor()
        cursor.execute(
            """
            INSERT INTO documents (document_id, filename, file_type, current_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (document_id, filename, file_type, 1, now, now),
        )
        self.sqlite.commit()

    def _update_document_version(self, document_id: str, version: int, now: str) -> None:
        cursor = self.sqlite.cursor()
        cursor.execute(
            "UPDATE documents SET current_version = ?, updated_at = ? WHERE document_id = ?",
            (version, now, document_id),
        )
        self.sqlite.commit()

    def _create_document_version(
        self,
        version_id: str,
        document_id: str,
        version: int,
        file_path: str,
        parsed_path: str,
        content_hash: str,
        created_at: str,
    ) -> None:
        cursor = self.sqlite.cursor()
        cursor.execute(
            """
            INSERT INTO document_versions (version_id, document_id, version, file_path, parsed_path, content_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (version_id, document_id, version, file_path, parsed_path, content_hash, created_at),
        )
        self.sqlite.commit()

    def _replace_chunks(self, document_id: str, version: int, chunks: List[Dict[str, Any]]) -> None:
        cursor = self.sqlite.cursor()
        cursor.execute("DELETE FROM chunks WHERE document_id = ? AND version = ?", (document_id, version))
        ids: List[str] = []
        docs: List[Document] = []
        for chunk in chunks:
            metadata = chunk["metadata"]
            cursor.execute(
                """
                INSERT INTO chunks (chunk_id, document_id, version, chunk_index, content, keywords, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk["chunk_id"],
                    document_id,
                    version,
                    chunk["chunk_index"],
                    chunk["content"],
                    chunk["keywords"],
                    json.dumps(metadata, ensure_ascii=False),
                ),
            )
            ids.append(chunk["chunk_id"])
            docs.append(Document(page_content=chunk["content"], metadata=metadata))
        self.sqlite.commit()
        if ids:
            if self.vector_enabled:
                try:
                    self.vector_store.delete(ids=ids)
                    self.vector_store.add_documents(documents=docs, ids=ids)
                except Exception:
                    logger.exception("Vector index update failed for document %s v%s, disable vector search", document_id, version)
                    self.vector_enabled = False

    def _replace_temporary_chunks(self, temp_document_id: str, chunks: List[Dict[str, Any]]) -> None:
        cursor = self.sqlite.cursor()
        old_rows = cursor.execute(
            "SELECT chunk_id FROM temporary_chunks WHERE temp_document_id = ?",
            (temp_document_id,),
        ).fetchall()
        old_ids = [row["chunk_id"] for row in old_rows]
        cursor.execute("DELETE FROM temporary_chunks WHERE temp_document_id = ?", (temp_document_id,))
        ids: List[str] = []
        docs: List[Document] = []
        for chunk in chunks:
            metadata = chunk["metadata"]
            cursor.execute(
                """
                INSERT INTO temporary_chunks (chunk_id, temp_document_id, chunk_index, content, keywords, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk["chunk_id"],
                    temp_document_id,
                    chunk["chunk_index"],
                    chunk["content"],
                    chunk["keywords"],
                    json.dumps(metadata, ensure_ascii=False),
                ),
            )
            ids.append(chunk["chunk_id"])
            docs.append(Document(page_content=chunk["content"], metadata=metadata))
        self.sqlite.commit()
        if self.vector_enabled:
            try:
                if old_ids:
                    self.vector_store.delete(ids=old_ids)
                if ids:
                    self.vector_store.add_documents(documents=docs, ids=ids)
            except Exception:
                logger.exception("Temporary vector index update failed for temp document %s, disable vector search", temp_document_id)
                self.vector_enabled = False

    def _build_chunks(
        self,
        text: str,
        document_id: str,
        version: int,
        filename: str,
        source: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        parts = self.splitter.split_text(text)
        chunks: List[Dict[str, Any]] = []
        metadata_extra = extra_metadata or {}
        for index, content in enumerate(parts):
            if source == "temporary":
                chunk_id = f"tmp_{document_id}_{index}"
            else:
                chunk_id = f"{document_id}_v{version}_{index}"
            metadata = {
                "document_id": document_id,
                "filename": filename,
                "version": version,
                "chunk_index": index,
                "chunk_id": chunk_id,
                "source": source,
            }
            metadata.update(metadata_extra)
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "chunk_index": index,
                    "content": content,
                    "keywords": self._keywords(content),
                    "metadata": metadata,
                }
            )
        return chunks

    def _store_raw_file(self, source_path: str, document_id: str, version: int, filename: str) -> str:
        target_dir = os.path.join(settings.RAW_STORAGE_DIR, document_id, f"v{version}")
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, filename)
        shutil.copy2(source_path, target_path)
        return target_path

    def _store_parsed_json(self, parsed: Dict[str, Any], document_id: str, version: int) -> str:
        target_dir = os.path.join(settings.PROCESSED_STORAGE_DIR, document_id)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f"v{version}.json")
        with open(target_path, "w", encoding="utf-8") as file:
            json.dump(parsed, file, ensure_ascii=False)
        return target_path

    def _store_temp_raw_file(self, source_path: str, temp_document_id: str, filename: str) -> str:
        target_dir = os.path.join(self.temp_raw_dir, temp_document_id)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, filename)
        shutil.copy2(source_path, target_path)
        return target_path

    def _store_temp_parsed_json(self, parsed: Dict[str, Any], temp_document_id: str) -> str:
        target_dir = os.path.join(self.temp_processed_dir, temp_document_id)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, "parsed.json")
        with open(target_path, "w", encoding="utf-8") as file:
            json.dump(parsed, file, ensure_ascii=False)
        return target_path

    def _create_temporary_document(
        self,
        temp_document_id: str,
        session_id: str,
        filename: str,
        file_type: str,
        status: str,
        created_at: str,
        updated_at: str,
        expires_at: str,
        file_path: str,
        parsed_path: str,
        content_hash: str,
        metadata: Dict[str, Any],
    ) -> None:
        cursor = self.sqlite.cursor()
        cursor.execute(
            """
            INSERT INTO temporary_documents (
                temp_document_id, session_id, filename, file_type, status, created_at, updated_at, expires_at,
                file_path, parsed_path, content_hash, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                temp_document_id,
                session_id,
                filename,
                file_type,
                status,
                created_at,
                updated_at,
                expires_at,
                file_path,
                parsed_path,
                content_hash,
                json.dumps(metadata, ensure_ascii=False),
            ),
        )
        self.sqlite.commit()

    def _update_temporary_status(self, temp_document_id: str, status: str) -> None:
        cursor = self.sqlite.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "UPDATE temporary_documents SET status = ?, updated_at = ? WHERE temp_document_id = ?",
            (status, now, temp_document_id),
        )
        self.sqlite.commit()

    def _sha256(self, file_path: str) -> str:
        digest = hashlib.sha256()
        with open(file_path, "rb") as file:
            for block in iter(lambda: file.read(65536), b""):
                digest.update(block)
        return digest.hexdigest()

    def _extract_temp_metadata(
        self,
        parsed: Dict[str, Any],
        file_path: str,
        filename: str,
        session_id: str,
    ) -> Dict[str, Any]:
        text = str(parsed.get("text", "") or "")
        sections = parsed.get("sections") or []
        return {
            "filename": filename,
            "session_id": session_id,
            "format": parsed.get("format"),
            "section_count": len(sections),
            "character_count": len(text),
            "keyword_preview": self._keywords(text),
            "file_size": os.path.getsize(file_path),
        }

    def _keywords(self, content: str) -> str:
        words = [word.strip("，。！？；：,.!?;:()[]{}\"'").lower() for word in content.split()]
        words = [word for word in words if len(word) >= 2]
        uniq = list(dict.fromkeys(words))
        return " ".join(uniq[:20])

    def _merge_search_results(
        self,
        semantic: List[Dict[str, Any]],
        fulltext: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}
        for item in semantic:
            chunk_id = item["chunk_id"]
            merged[chunk_id] = {
                "chunk_id": chunk_id,
                "score": float(item["score"]) * 0.7,
                "content": item["content"],
                "metadata": item["metadata"],
            }
        for item in fulltext:
            chunk_id = item["chunk_id"]
            if chunk_id in merged:
                merged[chunk_id]["score"] += float(item["score"]) * 0.3
            else:
                merged[chunk_id] = {
                    "chunk_id": chunk_id,
                    "score": float(item["score"]) * 0.3,
                    "content": item["content"],
                    "metadata": item["metadata"],
                }
        results = list(merged.values())
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _smart_rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        if not candidates:
            return []
        reranker = getattr(self, "reranker", None)
        if reranker is None:
            results = sorted(candidates, key=lambda x: float(x.get("score", 0.0)), reverse=True)
            return results[:top_k]
        pairs = [(query, str(item.get("content", ""))[:4000]) for item in candidates]
        batch_size = int(os.getenv("RERANKER_BATCH_SIZE") or getattr(settings, "RERANKER_BATCH_SIZE", 16) or 16)
        try:
            scores = reranker.predict(pairs, batch_size=batch_size)
        except Exception:
            logger.warning("CrossEncoder rerank failed", exc_info=True)
            results = sorted(candidates, key=lambda x: float(x.get("score", 0.0)), reverse=True)
            return results[:top_k]
        reranked: List[Dict[str, Any]] = []
        for item, score in zip(candidates, scores):
            reranked.append(
                {
                    "chunk_id": item["chunk_id"],
                    "score": float(score),
                    "content": item.get("content", ""),
                    "metadata": item.get("metadata", {}),
                }
            )
        deduped = self._deduplicate_by_content(reranked)
        deduped.sort(key=lambda x: x["score"], reverse=True)
        return deduped[:top_k]

    def _deduplicate_by_content(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: Dict[str, Dict[str, Any]] = {}
        for item in items:
            key = hashlib.md5(item.get("content", "").strip().encode("utf-8")).hexdigest()
            old = seen.get(key)
            if old is None or float(item.get("score", 0.0)) > float(old.get("score", 0.0)):
                seen[key] = item
        return list(seen.values())

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        length = min(len(vec_a), len(vec_b))
        dot = sum(vec_a[i] * vec_b[i] for i in range(length))
        norm_a = math.sqrt(sum(x * x for x in vec_a[:length]))
        norm_b = math.sqrt(sum(x * x for x in vec_b[:length]))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _query_terms(self, query: str) -> List[str]:
        normalized = query.strip().lower()
        if not normalized:
            return []
        terms: List[str] = []
        for token in re.findall(r"[0-9a-zA-Z\u4e00-\u9fff]+", normalized):
            if len(token) >= 2:
                terms.append(token)
            if len(token) >= 4:
                terms.extend(token[idx : idx + 2] for idx in range(0, len(token) - 1))
        uniq = list(dict.fromkeys(terms))
        return uniq[:20]

    def _keyword_overlap_score(self, query: str, content: str, terms: List[str]) -> float:
        query_lower = query.lower().strip()
        content_lower = content.lower()
        exact_hits = content_lower.count(query_lower) if query_lower else 0
        total_hits = 0.0
        matched_terms = 0
        for term in terms:
            hit = content_lower.count(term)
            if hit > 0:
                matched_terms += 1
                total_hits += min(float(hit), 3.0)
        coverage = (matched_terms / len(terms)) if terms else 0.0
        length_penalty = math.log(max(len(content_lower), 32), 2)
        return (exact_hits * 6.0 + total_hits * 1.8 + coverage * 4.0) / max(length_penalty, 1.0)

    def _fallback_recent_chunks(
        self,
        top_k: int,
        document_id: Optional[str] = None,
        temporary_document_ids: Optional[Sequence[str]] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cursor = self.sqlite.cursor()
        results: List[Dict[str, Any]] = []
        temp_params: List[Any] = []
        temp_conditions = ["td.status = 'indexed'"]
        if session_id:
            temp_conditions.append("td.session_id = ?")
            temp_params.append(session_id)
        temp_rows = cursor.execute(
            f"""
            SELECT tc.chunk_id, tc.content, tc.metadata_json
            FROM temporary_chunks tc
            JOIN temporary_documents td ON td.temp_document_id = tc.temp_document_id
            WHERE {' AND '.join(temp_conditions)}
            ORDER BY td.updated_at DESC, tc.chunk_index ASC
            LIMIT ?
            """,
            tuple(temp_params + [max(top_k * 4, 8)]),
        ).fetchall()
        id_set = set(temporary_document_ids or [])
        for row in temp_rows:
            metadata = json.loads(row["metadata_json"])
            if id_set and metadata.get("temp_document_id") not in id_set:
                continue
            results.append(
                {
                    "chunk_id": row["chunk_id"],
                    "score": 0.05,
                    "content": row["content"],
                    "metadata": metadata,
                }
            )
            if len(results) >= top_k:
                return results
        kb_conditions: List[str] = []
        kb_params: List[Any] = []
        if document_id:
            kb_conditions.append("document_id = ?")
            kb_params.append(document_id)
        where_clause = ""
        if kb_conditions:
            where_clause = "WHERE " + " AND ".join(kb_conditions)
        kb_rows = cursor.execute(
            f"""
            SELECT chunk_id, content, metadata_json
            FROM chunks
            {where_clause}
            ORDER BY rowid DESC
            LIMIT ?
            """,
            tuple(kb_params + [max(top_k * 4, 8)]),
        ).fetchall()
        for row in kb_rows:
            results.append(
                {
                    "chunk_id": row["chunk_id"],
                    "score": 0.01,
                    "content": row["content"],
                    "metadata": json.loads(row["metadata_json"]),
                }
            )
            if len(results) >= top_k:
                break
        return results[:top_k]

    def _generate_answer(
        self,
        query: str,
        results: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        require_llm: bool = False,
    ) -> str:
        context = "\n\n".join(
            [
                f"[{index + 1}] 来源={item['metadata'].get('source', 'knowledge_base')} 文件={item['metadata'].get('filename')} 片段={item['content'][:700]}"
                for index, item in enumerate(results)
            ]
        )
        history = self._get_session_messages(session_id, limit=6)
        need_more_info = self._suggest_missing_info(query, history)
        if need_more_info:
            if require_llm:
                raise RuntimeError("LLM is required but input is insufficient")
            return need_more_info
        if self.llm is None:
            self.llm = self._build_llm()
        if self.llm is None:
            if require_llm:
                raise RuntimeError("LLM is required but not configured")
            snippets = [item["content"][:180] for item in results]
            return "基于检索重排结果，建议回答如下：\n" + "\n".join(
                [f"{index + 1}. {snippet}" for index, snippet in enumerate(snippets)]
            )
        system_text = (
            "你是教学智能体的知识库问答助手。"
            "请严格根据提供的检索上下文回答问题，优先提炼教学目标、重点难点、教学流程和互动设计。"
            "如果上下文信息不足，明确说明不足点，并优先向用户提出最多3条具体补充问题，不要编造事实。"
        )
        history_text = self._render_history_for_prompt(history)
        user_text = (
            f"当前会话ID：{session_id or 'none'}\n"
            f"会话历史（最近几轮）：\n{history_text}\n\n"
            f"用户问题：{query}\n\n"
            f"检索上下文：\n{context}\n\n"
            "请输出简洁、结构化的中文答案。"
        )
        try:
            response = self.llm.invoke([SystemMessage(content=system_text), HumanMessage(content=user_text)])
            text = getattr(response, "content", "")
            if isinstance(text, str) and text.strip():
                return text.strip()
        except Exception as e:
            logger.exception("LLM answer generation failed, fallback to extractive response")
            if require_llm:
                raise RuntimeError(f"LLM invocation failed: {e}")
        snippets = [item["content"][:180] for item in results]
        return "基于检索重排结果，建议回答如下：\n" + "\n".join(
            [f"{index + 1}. {snippet}" for index, snippet in enumerate(snippets)]
        )
