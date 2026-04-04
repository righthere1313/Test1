#!/usr/bin/env python3
"""
API 连通性测试脚本（聚焦 chat.py 与 files.py 所在的端点）
功能：
- 自动发现 OpenAPI 中以 /api/v1/chat 与 /api/v1/files 开头的端点
- 对每个端点发起实际请求，测量响应时间、记录状态码与错误信息
- 若可获取到 JSON Schema，则进行响应体校验
- 生成 JSON 与 Markdown 报告，便于快速定位异常与排查
"""
from __future__ import annotations

import argparse
import io
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests

try:
    from jsonschema import Draft7Validator
except Exception:
    Draft7Validator = None

DEFAULT_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
DEFAULT_SPEC = os.environ.get("OPENAPI_URL", "/api/v1/openapi.json")
DEFAULT_TIMEOUT = int(os.environ.get("API_TIMEOUT", "15"))


def _is_json(ct: str) -> bool:
    if not ct:
        return False
    return "application/json" in ct or "+json" in ct


def load_openapi(session: requests.Session, spec_url: str, timeout: int) -> dict:
    r = session.get(spec_url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def pick_response_schema(op: dict) -> Optional[dict]:
    responses = (op or {}).get("responses", {})
    for code in ["200", "201", "202", "204", "default"]:
        if code in responses:
            content = responses[code].get("content", {})
            for mt, v in content.items():
                if "json" in mt and "schema" in v:
                    return v["schema"]
    for v in responses.values():
        content = v.get("content", {})
        for mt, vv in content.items():
            if "json" in mt and "schema" in vv:
                return vv["schema"]
    return None


def schema_validate(schema: dict, data: Any) -> Tuple[bool, Optional[str]]:
    if Draft7Validator is None or not schema:
        return True, None
    try:
        Draft7Validator(schema).validate(data)
        return True, None
    except Exception as e:
        return False, str(e)


def substitute_path_params(path: str, document_id: Optional[str], version: Optional[int]) -> str:
    doc_value = document_id or "nonexistent"
    ver_value = str(version if version is not None else 1)
    path = path.replace("{document_id}", doc_value)
    path = path.replace("{version}", ver_value)
    return path


def build_payload_for(endpoint_path: str, method: str) -> dict:
    # 针对 chat 与 files 的常用端点，构建最小可用的 payload
    if endpoint_path.startswith("/api/v1/chat"):
        if endpoint_path.endswith("/qa"):
            return {"query": "测试问题", "top_k": 3, "document_id": None, "temporary_document_ids": None, "session_id": "connectivity-test"}
        return {"query": "测试", "top_k": 3, "document_id": None}
    return {}


def build_files_for(endpoint_path: str) -> Optional[dict]:
    # 针对上传接口构造内存文件
    if "/upload" in endpoint_path:
        mem = io.BytesIO(b"connectivity test\nThis is a test file.")
        mem.name = "connectivity_test.txt"
        return {"file": ("connectivity_test.txt", mem, "text/plain")}
    return None


def build_form_for(endpoint_path: str) -> Optional[dict]:
    if endpoint_path.endswith("/upload/staging"):
        return {"session_id": "connectivity-test", "ttl_minutes": "60"}
    return None


def create_seed_document(session: requests.Session, base: str, timeout: int) -> Tuple[Optional[str], Optional[int]]:
    url = urljoin(base, "/api/v1/files/upload/kb")
    mem = io.BytesIO(b"connectivity seed\nThis is a test file.")
    mem.name = "connectivity_seed.txt"
    try:
        resp = session.post(url, files={"file": ("connectivity_seed.txt", mem, "text/plain")}, timeout=timeout)
        if resp.status_code not in (200, 201):
            return None, None
        data = resp.json()
        return data.get("document_id"), data.get("version")
    except Exception:
        return None, None


@dataclass
class EndpointDef:
    method: str
    path: str
    operation: dict


def collect_endpoints(spec: dict) -> List[EndpointDef]:
    endpoints: List[EndpointDef] = []
    paths = spec.get("paths", {})
    for path, item in paths.items():
        if not (path.startswith("/api/v1/chat") or path.startswith("/api/v1/files")):
            continue
        for m in ["get", "post", "put", "patch", "delete"]:
            if m in item:
                endpoints.append(EndpointDef(method=m.upper(), path=path, operation=item[m]))
    return endpoints


def test_endpoint(
    session: requests.Session,
    base: str,
    ep: EndpointDef,
    timeout: int,
    document_id: Optional[str],
    version: Optional[int],
) -> dict:
    method = ep.method
    raw_path = substitute_path_params(ep.path, document_id, version)
    url = urljoin(base, raw_path)
    payload = build_payload_for(ep.path, method)
    files = build_files_for(ep.path)
    form = build_form_for(ep.path)
    headers: Dict[str, str] = {}

    t0 = time.perf_counter()
    status = None
    ct = None
    isjson = None
    json_valid = None
    schema_valid = None
    error = None
    data = None

    try:
        if files:
            if form:
                resp = session.request(method, url, files=files, data=form, timeout=timeout, headers=headers)
            else:
                resp = session.request(method, url, files=files, timeout=timeout, headers=headers)
        else:
            if payload and method in {"POST", "PUT", "PATCH"}:
                resp = session.request(method, url, json=payload, timeout=timeout, headers=headers)
            else:
                resp = session.request(method, url, timeout=timeout, headers=headers)
        status = resp.status_code
        ct = resp.headers.get("Content-Type", "")
        isjson = _is_json(ct)
        if isjson:
            try:
                data = resp.json()
                json_valid = True
            except Exception as e:
                json_valid = False
                error = f"InvalidJSON: {e}"
        schema = pick_response_schema(ep.operation)
        if isjson and json_valid and schema:
            ok, serr = schema_validate(schema, data)
            schema_valid = ok
            if not ok and not error:
                error = f"SchemaError: {serr}"
    except Exception as e:
        error = f"RequestError: {e}"
    dt = int((time.perf_counter() - t0) * 1000)
    ok = error is None and status is not None and status in (200, 201, 202, 204)
    return {
        "method": method,
        "path": ep.path,
        "url": url,
        "status": status,
        "ok": ok,
        "duration_ms": dt,
        "content_type": ct,
        "is_json": isjson,
        "json_valid": json_valid,
        "schema_valid": schema_valid,
        "error": error,
        "payload": payload if payload else None,
    }


def make_markdown(report: dict) -> str:
    lines = []
    lines.append(f"# API 连通性测试报告")
    lines.append("")
    lines.append(f"- Base URL: {report.get('base_url')}")
    lines.append(f"- Started: {report.get('started_at')}")
    lines.append(f"- Elapsed: {report.get('elapsed_ms')} ms")
    lines.append("")
    summary = report.get("summary", {})
    lines.append(f"## 总览")
    lines.append(f"- 端点总数: {summary.get('total', 0)}")
    lines.append(f"- 成功: {summary.get('success', 0)}")
    lines.append(f"- 失败: {summary.get('failure', 0)}")
    lines.append("")
    if report.get("results"):
        lines.append("## 详细结果")
        for r in report["results"]:
            ok = "✅" if r["ok"] else "❌"
            lines.append(f"- {ok} [{r['method']}] {r['path']} -> {r.get('status')} in {r['duration_ms']}ms")
            if r.get("error"):
                lines.append(f"  - 错误: {r['error']}")
    lines.append("")
    lines.append("## 排查建议")
    lines.append("- 连接失败(RequestError): 检查服务是否已启动、地址/端口是否正确、网络是否可达")
    lines.append("- 404: 路由可能不存在或删除，请核对 chat.py/files.py 是否提供该端点，或路径参数是否有效")
    lines.append("- 405: 方法不匹配，核对实际端点允许的方法")
    lines.append("- 422: 入参不符合 Schema，请对照 OpenAPI 的请求体字段与类型")
    lines.append("- 500: 服务内部错误，建议查看应用日志并定位对应服务实现")
    lines.append("- SchemaError: 返回结构与 OpenAPI 定义不一致，需检查响应模型或文档")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE, help="Base URL, e.g. http://localhost:8000")
    ap.add_argument("--spec", default=DEFAULT_SPEC, help="OpenAPI spec path or absolute URL")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    ap.add_argument("--max", type=int, default=0, help="最多测试多少个端点（0 为不限制）")
    args = ap.parse_args()

    base = args.base
    spec_url = args.spec
    if not spec_url.startswith("http"):
        spec_url = urljoin(base, spec_url)

    session = requests.Session()
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    t0 = time.perf_counter()
    try:
        spec = load_openapi(session, spec_url, args.timeout)
        endpoints = collect_endpoints(spec)
    except Exception as e:
        # OpenAPI 加载失败时，回退到一组常用端点
        endpoints = [
            EndpointDef("POST", "/api/v1/chat/search/fulltext", {}),
            EndpointDef("POST", "/api/v1/chat/search/semantic", {}),
            EndpointDef("POST", "/api/v1/chat/search/hybrid", {}),
            EndpointDef("POST", "/api/v1/chat/qa", {}),
            EndpointDef("POST", "/api/v1/files/upload", {}),
            EndpointDef("POST", "/api/v1/files/upload/kb", {}),
            EndpointDef("POST", "/api/v1/files/upload/staging", {}),
            EndpointDef("GET", "/api/v1/files/staging/documents", {}),
            EndpointDef("GET", "/api/v1/files/documents", {}),
            EndpointDef("GET", "/api/v1/files/documents/{document_id}", {}),
            EndpointDef("GET", "/api/v1/files/documents/{document_id}/versions", {}),
            EndpointDef("GET", "/api/v1/files/documents/{document_id}/versions/{version}/download", {}),
        ]
        print(f"⚠️ OpenAPI 加载失败: {e}，使用默认端点集合继续测试")

    if args.max and len(endpoints) > args.max:
        endpoints = endpoints[: args.max]

    seed_document_id, seed_version = create_seed_document(session, base, args.timeout)
    results = []
    for ep in endpoints:
        r = test_endpoint(session, base, ep, args.timeout, seed_document_id, seed_version)
        results.append(r)

    elapsed = int((time.perf_counter() - t0) * 1000)
    summary = {
        "total": len(results),
        "success": sum(1 for r in results if r["ok"]),
        "failure": sum(1 for r in results if not r["ok"]),
    }
    report = {
        "base_url": base,
        "started_at": started,
        "elapsed_ms": elapsed,
        "summary": summary,
        "results": results,
    }
    os.makedirs("tests", exist_ok=True)
    jname = "tests/api_connectivity_report.json"
    mname = "tests/api_connectivity_report.md"
    with open(jname, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(mname, "w", encoding="utf-8") as f:
        f.write(make_markdown(report))

    print(f"完成: {summary['success']}/{summary['total']} OK, 详情见 {jname} 与 {mname}")


if __name__ == "__main__":
    main()
