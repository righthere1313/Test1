import hashlib
import json
import os
import sqlite3
import time
import uuid
from typing import Any

from app.core.config import settings


def _now_ts() -> int:
    return int(time.time())


class PPTPlanStore:
    def __init__(self) -> None:
        os.makedirs(os.path.dirname(settings.METADATA_DB_PATH), exist_ok=True)
        self.sqlite = sqlite3.connect(
            settings.METADATA_DB_PATH,
            check_same_thread=False,
            timeout=5.0,
        )
        self.sqlite.row_factory = sqlite3.Row
        try:
            self.sqlite.execute("PRAGMA journal_mode=WAL;")
            self.sqlite.execute("PRAGMA synchronous=NORMAL;")
            self.sqlite.execute("PRAGMA busy_timeout=5000;")
        except Exception:
            pass
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.sqlite.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ppt_projects (
                ppt_id TEXT PRIMARY KEY,
                layout TEXT NOT NULL,
                title TEXT NOT NULL,
                subtitle TEXT,
                current_version INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ppt_versions (
                ppt_version_id TEXT PRIMARY KEY,
                ppt_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                base_version INTEGER,
                session_id TEXT,
                instructions TEXT,
                plan_json TEXT NOT NULL,
                plan_hash TEXT NOT NULL,
                rendered_filename TEXT,
                created_at INTEGER NOT NULL,
                UNIQUE(ppt_id, version)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ppt_versions_ppt_id ON ppt_versions(ppt_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ppt_versions_ppt_id_version ON ppt_versions(ppt_id, version)")
        self.sqlite.commit()

    def _hash_plan(self, plan: dict) -> str:
        raw = json.dumps(plan, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()

    def create_project_with_version(
        self,
        *,
        layout: str,
        title: str,
        subtitle: str | None,
        plan: dict,
        session_id: str | None = None,
        instructions: str | None = None,
    ) -> tuple[str, int, str]:
        ppt_id = uuid.uuid4().hex
        version = 1
        plan_hash = self._hash_plan(plan)
        plan_json = json.dumps(plan, ensure_ascii=False)
        now = _now_ts()
        pv_id = uuid.uuid4().hex
        cur = self.sqlite.cursor()
        cur.execute("BEGIN")
        try:
            cur.execute(
                "INSERT INTO ppt_projects(ppt_id, layout, title, subtitle, current_version, created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
                (ppt_id, str(layout), str(title), subtitle, version, now, now),
            )
            cur.execute(
                "INSERT INTO ppt_versions(ppt_version_id, ppt_id, version, base_version, session_id, instructions, plan_json, plan_hash, rendered_filename, created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (pv_id, ppt_id, version, None, session_id, instructions, plan_json, plan_hash, None, now),
            )
            self.sqlite.commit()
        except Exception:
            self.sqlite.rollback()
            raise
        return ppt_id, version, pv_id

    def get_project(self, ppt_id: str) -> dict | None:
        cur = self.sqlite.cursor()
        row = cur.execute("SELECT * FROM ppt_projects WHERE ppt_id = ?", (ppt_id,)).fetchone()
        return dict(row) if row else None

    def get_plan(self, ppt_id: str, version: int | None = None) -> dict | None:
        v = int(version) if version else None
        cur = self.sqlite.cursor()
        if v is None:
            row = cur.execute(
                "SELECT v.plan_json FROM ppt_versions v JOIN ppt_projects p ON v.ppt_id=p.ppt_id AND v.version=p.current_version WHERE v.ppt_id=?",
                (ppt_id,),
            ).fetchone()
        else:
            row = cur.execute("SELECT plan_json FROM ppt_versions WHERE ppt_id=? AND version=?", (ppt_id, v)).fetchone()
        if not row:
            return None
        try:
            obj = json.loads(row["plan_json"])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    def create_new_version(
        self,
        *,
        ppt_id: str,
        base_version: int,
        plan: dict,
        session_id: str | None = None,
        instructions: str | None = None,
    ) -> tuple[int, str]:
        cur = self.sqlite.cursor()
        now = _now_ts()
        cur.execute("BEGIN")
        try:
            proj = cur.execute("SELECT current_version FROM ppt_projects WHERE ppt_id=?", (ppt_id,)).fetchone()
            if not proj:
                raise ValueError("ppt_id not found")
            cur_ver = int(proj["current_version"])
            if int(base_version) != cur_ver:
                raise ValueError("base_version mismatch")
            new_ver = cur_ver + 1
            pv_id = uuid.uuid4().hex
            plan_hash = self._hash_plan(plan)
            plan_json = json.dumps(plan, ensure_ascii=False)
            cur.execute(
                "INSERT INTO ppt_versions(ppt_version_id, ppt_id, version, base_version, session_id, instructions, plan_json, plan_hash, rendered_filename, created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (pv_id, ppt_id, new_ver, cur_ver, session_id, instructions, plan_json, plan_hash, None, now),
            )
            cur.execute("UPDATE ppt_projects SET current_version=?, updated_at=? WHERE ppt_id=?", (new_ver, now, ppt_id))
            self.sqlite.commit()
        except Exception:
            self.sqlite.rollback()
            raise
        return new_ver, pv_id

    def set_rendered_filename(self, *, ppt_id: str, version: int, filename: str) -> None:
        cur = self.sqlite.cursor()
        cur.execute(
            "UPDATE ppt_versions SET rendered_filename=? WHERE ppt_id=? AND version=?",
            (str(filename), str(ppt_id), int(version)),
        )
        self.sqlite.commit()

    def get_session_messages(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        sid = str(session_id or "").strip()
        if not sid:
            return []
        lim = max(1, min(int(limit), 50))
        cur = self.sqlite.cursor()
        rows = cur.execute(
            "SELECT role, content, created_at FROM conversation_messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (sid, lim),
        ).fetchall()
        out = []
        for r in reversed(list(rows or [])):
            out.append({"role": r["role"], "content": r["content"], "created_at": r["created_at"]})
        return out

