import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=180) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8", errors="ignore"))


def _get_bytes(url: str) -> bytes:
    req = Request(url, headers={"Accept": "*/*"}, method="GET")
    with urlopen(req, timeout=180) as resp:
        return resp.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="TA服务地址，例如 http://127.0.0.1:8000")
    parser.add_argument("--layout", default=None, help="可选：仅用于说明，不影响docx生成")
    args = parser.parse_args()

    base_url = str(args.base_url).rstrip("/")
    endpoint = f"{base_url}/api/v1/generate/docx/auto"

    run_id = str(int(time.time()))
    payload = {
        "topic": "勾股定理",
        "title": f"勾股定理教案-{run_id}",
        "extra_instructions": (
            "面向初中学生。给出定义、推导思路、例题讲解、常见误区、课堂活动设计与课后练习。"
            "每个章节至少2条要点，语言具体可执行。"
        ),
    }

    try:
        resp = _post_json(endpoint, payload)
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
        raise SystemExit(f"HTTPError: {e.code} {detail}")
    except URLError as e:
        raise SystemExit(f"URLError: {e}")

    url = resp.get("download_url")
    if not isinstance(url, str) or not url.startswith("/"):
        raise SystemExit(f"invalid response: {resp}")

    file_bytes = _get_bytes(f"{base_url}{url}")
    if not file_bytes.startswith(b"PK"):
        raise SystemExit("downloaded file is not a docx (zip header missing)")

    out = Path(__file__).resolve().parent / f"docx_pythagoras_{run_id}.docx"
    out.write_bytes(file_bytes)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

