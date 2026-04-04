import os
import sys
from pathlib import Path

import httpx


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base_dir))

    base_url = os.getenv("BASE_URL", "").strip().rstrip("/")
    if base_url:
        r = httpx.get(f"{base_url}/api/v1/templates/layouts", timeout=20)
        r.raise_for_status()
        layouts = r.json()
    else:
        from app.main import app
        from fastapi.testclient import TestClient

        tc = TestClient(app)
        with httpx.Client(base_url=str(tc.base_url), transport=tc._transport, timeout=20) as client:  # type: ignore[attr-defined]
            r = client.get("/api/v1/templates/layouts")
            if r.status_code != 200:
                raise SystemExit(f"request failed: {r.status_code} {r.text}")
            layouts = r.json()

    if not isinstance(layouts, list):
        raise SystemExit(f"unexpected response: {layouts}")

    layouts = [str(x) for x in layouts if str(x).strip()]
    layouts.sort()

    print(f"[+] layouts ({len(layouts)}):")
    for name in layouts:
        print("-", name)


if __name__ == "__main__":
    main()

