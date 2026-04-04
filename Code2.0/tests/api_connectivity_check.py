#!/usr/bin/env python3
import argparse
import json
import time
import re
from urllib.parse import urljoin

import requests

try:
    import yaml
except Exception:
    yaml = None

try:
    from jsonschema import Draft7Validator, RefResolver
except Exception:
    Draft7Validator = None
    RefResolver = None

METHODS = ["get", "post", "put", "patch", "delete", "head", "options"]


def _is_json(ct: str) -> bool:
    if not ct:
        return False
    return "application/json" in ct or "+json" in ct


def load_openapi(spec_url: str, timeout: int, headers: dict) -> dict:
    r = requests.get(spec_url, timeout=timeout, headers=headers)
    r.raise_for_status()
    text = r.text
    if spec_url.endswith((".yaml", ".yml")):
        if yaml is None:
            raise RuntimeError("pyyaml not installed")
        spec = yaml.safe_load(text)
    else:
        spec = r.json()
    paths = spec.get("paths", {})
    servers = []
    for s in spec.get("servers", []):
        u = s.get("url")
        if u:
            servers.append(u)
    endpoints = []
    for path, item in paths.items():
        for m in METHODS:
            if m in item:
                endpoints.append({"method": m.upper(), "path": path, "op": item[m]})
    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    return {"endpoints": endpoints, "servers": servers, "raw": spec, "schemas": schemas}


def substitute_path_params(path: str) -> str:
    def repl(m):
        name = m.group(1)
        if "id" in name.lower():
            return "1"
        if "uuid" in name.lower():
            return "00000000-0000-0000-0000-000000000000"
        if "date" in name.lower():
            return "2020-01-01"
        return "sample"

    return re.sub(r"\{([^{}]+)\}", repl, path)


def pick_response_schema(op: dict):
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


def build_headers(auth_header: str, extra_headers: list) -> dict:
    h = {}
    if auth_header:
        if " " in auth_header:
            k, v = auth_header.split(" ", 1)
            if k.lower() == "authorization":
                h["Authorization"] = v
            else:
                h[k] = v
        else:
            h["Authorization"] = auth_header
    if extra_headers:
        for kv in extra_headers:
            k, v = kv.split(":", 1)
            h[k.strip()] = v.strip()
    return h


def validate_json_schema(instance, schema, resolver_base=None):
    if Draft7Validator is None:
        return {"schema_valid": None, "error": None}
    try:
        resolver = RefResolver(base_uri=resolver_base or "", referrer=schema)
        Draft7Validator(schema, resolver=resolver).validate(instance)
        return {"schema_valid": True, "error": None}
    except Exception as e:
        return {"schema_valid": False, "error": str(e)}


def test_endpoint(session, base_url, ep, headers, timeout, schema=None):
    method = ep["method"]
    raw_path = ep["path"]
    path = substitute_path_params(raw_path)
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    req_headers = dict(headers)
    t0 = time.perf_counter()
    status = None
    ct = None
    isjson = None
    json_valid = None
    schema_valid = None
    error = None
    try:
        resp = session.request(method, url, timeout=timeout, headers=req_headers)
        dt = int((time.perf_counter() - t0) * 1000)
        status = resp.status_code
        ct = resp.headers.get("Content-Type", "")
        if _is_json(ct):
            isjson = True
            try:
                data = resp.json()
                json_valid = True
                if schema:
                    sv = validate_json_schema(data, schema)
                    schema_valid = sv["schema_valid"]
                    if sv["error"]:
                        error = f"SchemaError: {sv['error']}"
            except Exception as e:
                json_valid = False
                error = f"JSONParseError: {e}"
        else:
            isjson = False
        ok = 200 <= status < 300
        return {
            "method": method,
            "url": url,
            "status": status,
            "ok": ok,
            "duration_ms": dt,
            "content_type": ct,
            "is_json": isjson,
            "json_valid": json_valid,
            "schema_valid": schema_valid,
            "error": error,
            "path": raw_path,
        }
    except Exception as e:
        dt = int((time.perf_counter() - t0) * 1000)
        return {
            "method": method,
            "url": url,
            "status": status,
            "ok": False,
            "duration_ms": dt,
            "content_type": ct,
            "is_json": isjson,
            "json_valid": json_valid,
            "schema_valid": schema_valid,
            "error": f"RequestError: {e}",
            "path": raw_path,
        }


def probe_error_handling(session, base_url, headers, timeout):
    url = urljoin(base_url.rstrip("/") + "/", "__connectivity_probe__")
    t0 = time.perf_counter()
    try:
        r = session.get(url, headers=headers, timeout=timeout)
        dt = int((time.perf_counter() - t0) * 1000)
        ct = r.headers.get("Content-Type", "")
        info = {"status": r.status_code, "duration_ms": dt, "content_type": ct}
        if _is_json(ct):
            try:
                data = r.json()
                info["is_json"] = True
                info["json_valid"] = True
                info["body_keys"] = list(data) if isinstance(data, dict) else None
            except Exception:
                info["is_json"] = True
                info["json_valid"] = False
        else:
            info["is_json"] = False
        return {"url": url, "result": info}
    except Exception as e:
        dt = int((time.perf_counter() - t0) * 1000)
        return {"url": url, "result": {"status": None, "duration_ms": dt, "error": str(e)}}


def make_markdown(report: dict) -> str:
    lines = []
    lines.append("# API 连通性测试报告")
    lines.append("")
    lines.append(f"- 目标基址: {report['base_url']}")
    lines.append(f"- 开始时间: {report['started_at']}")
    lines.append(f"- 耗时: {report['elapsed_ms']} ms")
    lines.append(
        f"- 端点总数: {report['summary']['total']}  成功: {report['summary']['success']}  失败: {report['summary']['failure']}"
    )
    lines.append("")
    lines.append("## 慢接口 Top 10")
    slow = sorted(report["results"], key=lambda x: x["duration_ms"], reverse=True)[:10]
    for r in slow:
        lines.append(f"- {r['method']} {r['url']}  {r['duration_ms']} ms  {'OK' if r['ok'] else 'FAIL'}")
    lines.append("")
    lines.append("## 失败详情")
    fails = [r for r in report["results"] if not r["ok"]]
    if not fails:
        lines.append("- 无")
    else:
        for r in fails:
            lines.append(
                f"- {r['method']} {r['url']} → {r['status']}  用时 {r['duration_ms']} ms  错误: {r.get('error')}"
            )
    lines.append("")
    lines.append("## 逐端点结果")
    for r in report["results"]:
        lines.append(
            f"- {r['method']} {r['url']} | {r['status']} | {r['duration_ms']} ms | {r['content_type']} | is_json={r['is_json']} | json_valid={r['json_valid']} | schema_valid={r['schema_valid']} | {'OK' if r['ok'] else 'FAIL'}"
        )
    if report.get("error_probe"):
        lines.append("")
        lines.append("## 错误处理探测")
        ep = report["error_probe"]
        lines.append(f"- 探测URL: {ep['url']}")
        lines.append(f"- 结果: {json.dumps(ep['result'], ensure_ascii=False)}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--openapi", action="append")
    ap.add_argument("--header", action="append")
    ap.add_argument("--auth")
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--negative", action="store_true")
    ap.add_argument("--max", type=int, default=0)
    args = ap.parse_args()

    headers = build_headers(args.auth, args.header)
    session = requests.Session()
    endpoints = []
    schemas_map = {}
    servers = []
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    t0 = time.perf_counter()

    if args.openapi:
        for spec in args.openapi:
            try:
                info = load_openapi(spec, args.timeout, headers)
                servers += info.get("servers", [])
                for ep in info["endpoints"]:
                    endpoints.append(ep)
                    s = pick_response_schema(ep.get("op"))
                    if s:
                        key = f"{ep['method']} {ep['path']}"
                        schemas_map[key] = s
            except Exception as e:
                print(f"加载 OpenAPI 失败: {spec}: {e}")

    uniq = {}
    for ep in endpoints:
        k = f"{ep['method']} {ep['path']}"
        uniq[k] = ep
    endpoints = list(uniq.values())
    if args.max and len(endpoints) > args.max:
        endpoints = endpoints[: args.max]

    results = []
    for ep in endpoints:
        schema = schemas_map.get(f"{ep['method']} {ep['path']}")
        r = test_endpoint(session, args.base, ep, headers, args.timeout, schema)
        results.append(r)

    probe = None
    if args.negative:
        probe = probe_error_handling(session, args.base, headers, args.timeout)

    elapsed = int((time.perf_counter() - t0) * 1000)
    summary = {
        "total": len(results),
        "success": sum(1 for r in results if r["ok"]),
        "failure": sum(1 for r in results if not r["ok"]),
    }

    report = {
        "base_url": args.base,
        "servers_from_spec": servers,
        "started_at": started,
        "elapsed_ms": elapsed,
        "summary": summary,
        "results": results,
        "error_probe": probe,
    }

    jname = "api_connectivity_report.json"
    mname = "api_connectivity_report.md"
    with open(jname, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(mname, "w", encoding="utf-8") as f:
        f.write(make_markdown(report))

    print(f"完成: {summary['success']}/{summary['total']} OK, 详情见 {jname} 与 {mname}")


if __name__ == "__main__":
    main()
