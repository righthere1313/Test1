import os
import time

import httpx


def main() -> None:
    base_url = os.getenv("BASE_URL", "").strip().rstrip("/") or "http://127.0.0.1:8000"
    timeout = httpx.Timeout(60.0, connect=10.0)

    payload_normal = {"query": "请用一句话解释什么是人工智能？", "top_k": 3, "session_id": f"smoke-{int(time.time())}"}
    payload_ppt = {
        "query": "请生成一份人工智能导论课件，15页左右。",
        "top_k": 3,
        "session_id": f"smoke-{int(time.time())}",
        "intent": "generate_ppt",
        "task_payload": {
            "slides_total": 15,
            "title": "人工智能导论",
            "subtitle": "chat/qa 触发生成",
        },
    }

    with httpx.Client(base_url=base_url, timeout=timeout, trust_env=False) as client:
        r1 = client.post("/api/v1/chat/qa", json=payload_normal)
        print("normal_chat status:", r1.status_code)
        print("normal_chat body:", r1.text[:500])
        r1.raise_for_status()

        r2 = client.post("/api/v1/chat/qa", json=payload_ppt)
        print("generate_ppt status:", r2.status_code)
        print("generate_ppt body:", r2.text[:800])
        r2.raise_for_status()


if __name__ == "__main__":
    main()

