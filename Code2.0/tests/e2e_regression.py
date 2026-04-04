import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from fastapi.testclient import TestClient


def _now_ms() -> int:
    return int(time.time() * 1000)


def _elapsed_ms(start: float, end: float) -> int:
    return int((end - start) * 1000)


def _request_with_timing(client: TestClient, method: str, url: str, **kwargs: Any) -> Tuple[int, Dict[str, Any], int]:
    start = time.perf_counter()
    response = client.request(method, url, **kwargs)
    end = time.perf_counter()
    payload: Dict[str, Any] = {}
    if response.headers.get("content-type", "").startswith("application/json"):
        payload = response.json()
    return response.status_code, payload, _elapsed_ms(start, end)


def _write_report(report: Dict[str, Any], base_dir: Path) -> None:
    json_path = base_dir / "tests" / "e2e_regression_report.json"
    md_path = base_dir / "tests" / "e2e_regression_report.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    lines = [
        "# 端到端回归测试报告",
        "",
        f"- Started: {report.get('started_at')}",
        f"- Duration: {report.get('duration_ms')} ms",
        f"- Pass Rate: {report.get('pass_rate')}%",
        "",
        "## 覆盖率分析",
        f"- 端点覆盖: {report['coverage']['endpoint_passed']}/{report['coverage']['endpoint_total']}",
        f"- 功能覆盖: {report['coverage']['feature_passed']}/{report['coverage']['feature_total']}",
        "",
        "## 性能指标",
        f"- Avg Latency: {report['performance']['avg_ms']} ms",
        f"- Min Latency: {report['performance']['min_ms']} ms",
        f"- Max Latency: {report['performance']['max_ms']} ms",
        "",
        "## 详细结果",
    ]
    for item in report["results"]:
        status = "✅" if item["ok"] else "❌"
        lines.append(f"- {status} [{item['method']}] {item['path']} -> {item['status']} in {item['duration_ms']}ms")
    lines.append("")
    lines.append("## 问题修复验证结果")
    lines.append(f"- LLM 初始化可用: {report['fix_verification']['llm_available']}")
    lines.append(f"- CrossEncoder 可用: {report['fix_verification']['reranker_available']}")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base_dir))
    load_dotenv(dotenv_path=base_dir / ".env")
    from app.main import app
    from app.services.knowledge_base_service import KnowledgeBaseService
    client = TestClient(app)
    started = _now_ms()

    kb_content = "教学目标\n重点内容\n课堂互动设计\n"
    temp_content = "临时文档：教学目标是理解函数式思维，重点是课堂互动。"
    files_kb = {"file": ("kb.txt", kb_content.encode("utf-8"), "text/plain")}
    files_temp = {"file": ("temp.txt", temp_content.encode("utf-8"), "text/plain")}

    results: List[Dict[str, Any]] = []

    status, payload, duration = _request_with_timing(client, "POST", "/api/v1/files/upload/kb", files=files_kb)
    results.append({"method": "POST", "path": "/api/v1/files/upload/kb", "status": status, "ok": status == 201, "duration_ms": duration})
    document_id = payload.get("document_id")

    status, payload, duration = _request_with_timing(
        client,
        "POST",
        "/api/v1/files/upload/staging",
        files=files_temp,
        data={"session_id": "e2e-session", "ttl_minutes": "60"},
    )
    results.append({"method": "POST", "path": "/api/v1/files/upload/staging", "status": status, "ok": status == 201, "duration_ms": duration})
    temp_document_id = payload.get("temp_document_id")

    status, payload, duration = _request_with_timing(
        client,
        "GET",
        "/api/v1/files/staging/documents",
        params={"session_id": "e2e-session"},
    )
    ok = status == 200 and any(item.get("temp_document_id") == temp_document_id for item in payload or [])
    results.append({"method": "GET", "path": "/api/v1/files/staging/documents", "status": status, "ok": ok, "duration_ms": duration})

    for path in ["/api/v1/chat/search/fulltext", "/api/v1/chat/search/semantic", "/api/v1/chat/search/hybrid"]:
        status, payload, duration = _request_with_timing(
            client,
            "POST",
            path,
            json={"query": "教学目标", "top_k": 3, "document_id": document_id},
        )
        ok = status == 200 and isinstance(payload.get("results"), list)
        results.append({"method": "POST", "path": path, "status": status, "ok": ok, "duration_ms": duration})

    status, payload, duration = _request_with_timing(
        client,
        "POST",
        "/api/v1/chat/qa",
        json={
            "query": "这节课的教学目标是什么？",
            "top_k": 3,
            "temporary_document_ids": [temp_document_id] if temp_document_id else None,
            "session_id": "e2e-session",
            "document_id": document_id,
        },
    )
    ok = status == 200 and bool(payload.get("answer")) and isinstance(payload.get("citations"), list)
    results.append({"method": "POST", "path": "/api/v1/chat/qa", "status": status, "ok": ok, "duration_ms": duration})

    durations = [item["duration_ms"] for item in results]
    pass_count = sum(1 for item in results if item["ok"])
    total = len(results)
    pass_rate = round(pass_count / total * 100, 2) if total else 0.0

    service = KnowledgeBaseService()
    report = {
        "started_at": started,
        "duration_ms": _elapsed_ms(started / 1000.0, time.time()),
        "pass_rate": pass_rate,
        "results": results,
        "coverage": {
            "endpoint_total": total,
            "endpoint_passed": pass_count,
            "feature_total": 5,
            "feature_passed": sum(
                1
                for ok in [
                    any(r["path"] == "/api/v1/files/upload/kb" and r["ok"] for r in results),
                    any(r["path"] == "/api/v1/files/upload/staging" and r["ok"] for r in results),
                    any("search" in r["path"] and r["ok"] for r in results),
                    any(r["path"] == "/api/v1/chat/qa" and r["ok"] for r in results),
                    any(r["path"] == "/api/v1/files/staging/documents" and r["ok"] for r in results),
                ]
                if ok
            ),
        },
        "performance": {
            "avg_ms": round(sum(durations) / len(durations), 2) if durations else 0,
            "min_ms": min(durations) if durations else 0,
            "max_ms": max(durations) if durations else 0,
        },
        "fix_verification": {
            "llm_available": service.llm is not None,
            "reranker_available": getattr(service, "reranker", None) is not None,
        },
    }
    _write_report(report, base_dir)

    if pass_count != total:
        raise SystemExit("E2E regression failed")


if __name__ == "__main__":
    main()
