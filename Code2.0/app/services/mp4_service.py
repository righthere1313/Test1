import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings


@dataclass(frozen=True)
class MP4Options:
    portrait_path: str | None = None
    voice: str = "Cherry"
    tts_model: str = "qwen3-tts-flash"
    llm_model: str = "qwen-turbo"
    video_model: str = "wan2.2-s2v"
    resolution: str = "480P"
    max_wait_seconds: int = 1800


class MP4Service:
    OUTPUT_DIR = str((Path(__file__).resolve().parents[3] / "data" / "generated" / "MP4").resolve())

    def __init__(self) -> None:
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    def create_job_id(self) -> str:
        return f"mp4_{uuid.uuid4().hex}"

    def job_dir(self, job_id: str) -> str:
        return os.path.join(self.OUTPUT_DIR, job_id)

    def meta_path(self, job_id: str) -> str:
        return os.path.join(self.job_dir(job_id), "meta.json")

    def script_path(self, job_id: str) -> str:
        return os.path.join(self.job_dir(job_id), "script.json")

    def pages_dir(self, job_id: str) -> str:
        return os.path.join(self.job_dir(job_id), "video")

    def audio_dir(self, job_id: str) -> str:
        return os.path.join(self.job_dir(job_id), "audio")

    def page_video_path(self, job_id: str, page: int) -> str:
        return os.path.join(self.pages_dir(job_id), f"page_{int(page)}.mp4")

    def init_meta(self, *, job_id: str, total_pages: int) -> dict:
        now = int(time.time())
        pages = {}
        for i in range(1, int(total_pages) + 1):
            pages[str(i)] = {"status": "queued", "error": None}
        meta = {
            "job_id": job_id,
            "mode": "per_page",
            "status": "queued",
            "total_pages": int(total_pages),
            "progress": {"done_pages": 0, "total_pages": int(total_pages)},
            "pages": pages,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        self._write_meta(job_id, meta)
        return meta

    def load_meta(self, job_id: str) -> dict | None:
        p = self.meta_path(job_id)
        if not os.path.exists(p):
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    def update_meta(self, job_id: str, patch: dict) -> dict | None:
        meta = self.load_meta(job_id) or {}
        if not isinstance(meta, dict):
            meta = {}
        for k, v in (patch or {}).items():
            meta[k] = v
        meta["updated_at"] = int(time.time())
        self._write_meta(job_id, meta)
        return meta

    def _write_meta(self, job_id: str, meta: dict) -> None:
        d = self.job_dir(job_id)
        os.makedirs(d, exist_ok=True)
        tmp = os.path.join(d, f".meta.{uuid.uuid4().hex}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
        os.replace(tmp, self.meta_path(job_id))

    def run(self, *, job_id: str, slides: list[dict], options: MP4Options) -> None:
        total_pages = len(slides)
        self.init_meta(job_id=job_id, total_pages=total_pages)
        self.update_meta(job_id, {"status": "processing"})

        pages_dir = self.pages_dir(job_id)
        audio_dir = self.audio_dir(job_id)
        os.makedirs(pages_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        try:
            portrait = self._resolve_portrait_path(options.portrait_path)
            narrations = self._generate_narrations(slides, llm_model=options.llm_model)
            self._write_script(job_id, slides, narrations)

            pages_meta = self.load_meta(job_id) or {}
            pages_state = pages_meta.get("pages") if isinstance(pages_meta.get("pages"), dict) else {}
            failures = 0
            for i, text in enumerate(narrations, start=1):
                pages_state[str(i)] = {"status": "processing", "error": None}
                self.update_meta(job_id, {"pages": pages_state})
                audio_path = os.path.join(audio_dir, f"audio_{i}.mp3")
                part_path = self.page_video_path(job_id, i)
                try:
                    self._generate_single_slide_video(
                        narration=text,
                        slide_index=i,
                        portrait_path=portrait,
                        audio_path=audio_path,
                        video_path=part_path,
                        voice=options.voice,
                        tts_model=options.tts_model,
                        video_model=options.video_model,
                        resolution=options.resolution,
                        max_wait_seconds=options.max_wait_seconds,
                    )
                    pages_state[str(i)] = {"status": "done", "error": None}
                except Exception as e:
                    failures += 1
                    pages_state[str(i)] = {"status": "failed", "error": {"code": "MP4_PAGE_FAILED", "message": str(e)}}
                done_pages = sum(1 for v in (pages_state or {}).values() if isinstance(v, dict) and v.get("status") == "done")
                self.update_meta(job_id, {"pages": pages_state, "progress": {"done_pages": done_pages, "total_pages": total_pages}})

            if failures > 0:
                done_pages = sum(1 for v in (pages_state or {}).values() if isinstance(v, dict) and v.get("status") == "done")
                self.update_meta(
                    job_id,
                    {
                        "status": "failed",
                        "progress": {"done_pages": done_pages, "total_pages": total_pages},
                        "error": {"code": "MP4_PARTIAL_FAILED", "message": f"{failures} pages failed"},
                    },
                )
            else:
                self.update_meta(job_id, {"status": "done", "progress": {"done_pages": total_pages, "total_pages": total_pages}})
        except Exception as e:
            self.update_meta(job_id, {"status": "failed", "error": {"code": "MP4_FAILED", "message": str(e)}})

    def _resolve_portrait_path(self, portrait_path: str | None) -> str:
        raw = str(portrait_path or "").strip()
        if raw:
            p = Path(raw)
            if not p.is_absolute():
                repo_root = Path(__file__).resolve().parents[3]
                p = (repo_root / raw).resolve()
            if p.exists() and p.is_file():
                return str(p)
        repo_root = Path(__file__).resolve().parents[3]
        default = (repo_root / "shuziren" / "D0464729ACBB9FFB3A3F577A92C246DF.jpg").resolve()
        if default.exists():
            return str(default)
        raise FileNotFoundError("portrait image not found")

    def _generate_narrations(self, slides: list[dict], *, llm_model: str) -> list[str]:
        api_key = (os.getenv("DASHSCOPE_API_KEY") or settings.DASHSCOPE_API_KEY or "").strip()
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required")

        try:
            import dashscope
        except Exception as e:
            raise RuntimeError(f"dashscope is required: {e}")

        dashscope.api_key = api_key
        texts: list[str] = []
        for idx, slide in enumerate(slides, start=1):
            title = str(slide.get("title") or "").strip()
            content = slide.get("content") or []
            if isinstance(content, list):
                content_str = "；".join([str(x) for x in content if str(x).strip()])
            else:
                content_str = str(content)
            notes = str(slide.get("notes") or "").strip()
            prompt = (
                f"你是一位亲切专业的老师，正在给学生讲课。请为PPT的第{idx}页生成一段讲课口播文案（约80-120字）。\n"
                "要求：\n"
                "- 严格控制在60-80字以内（非常重要，不能超过80字）\n"
                "- 语气亲切自然，像真实课堂一样\n"
                "- 适当加入过渡语（如\"接下来我们看\"\"大家注意\"）\n"
                "- 结合页面内容讲解，不要照本宣科\n"
                "\n"
                "页面内容：\n"
                f"- 标题：{title}\n"
                f"- 正文：{content_str or '无'}\n"
                f"- 备注：{notes or '无'}\n"
                "\n"
                "请直接输出讲课口播文案，不要加任何解释。"
            )
            resp = dashscope.Generation.call(
                model=llm_model,
                messages=[
                    {"role": "system", "content": "你是一位亲切自然的老师，讲课口语化、流畅、有亲和力，像真实课堂一样。"},
                    {"role": "user", "content": prompt},
                ],
            )
            if getattr(resp, "status_code", None) != 200 or getattr(resp, "output", None) is None:
                raise RuntimeError(f"narration generation failed at page {idx}")
            text = str(getattr(resp.output, "text", "") or "").strip()
            if not text:
                raise RuntimeError(f"empty narration at page {idx}")
            texts.append(text)
        return texts

    def _write_script(self, job_id: str, slides: list[dict], narrations: list[str]) -> None:
        out = self.script_path(job_id)
        data = {"job_id": job_id, "slides": slides, "narrations": narrations}
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_single_slide_video(
        self,
        *,
        narration: str,
        slide_index: int,
        portrait_path: str,
        audio_path: str,
        video_path: str,
        voice: str,
        tts_model: str,
        video_model: str,
        resolution: str,
        max_wait_seconds: int,
    ) -> None:
        dashscope_key = (os.getenv("DASHSCOPE_API_KEY") or settings.DASHSCOPE_API_KEY or "").strip()
        if not dashscope_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required")

        oss_access_key_id = (os.getenv("OSS_ACCESS_KEY_ID") or settings.OSS_ACCESS_KEY_ID or "").strip()
        oss_access_key_secret = (os.getenv("OSS_ACCESS_KEY_SECRET") or settings.OSS_ACCESS_KEY_SECRET or "").strip()
        oss_bucket_name = (os.getenv("OSS_BUCKET_NAME") or settings.OSS_BUCKET_NAME or "").strip()
        oss_endpoint = (os.getenv("OSS_ENDPOINT") or settings.OSS_ENDPOINT or "").strip()
        if not all([oss_access_key_id, oss_access_key_secret, oss_bucket_name, oss_endpoint]):
            raise RuntimeError("OSS_ACCESS_KEY_ID/OSS_ACCESS_KEY_SECRET/OSS_BUCKET_NAME/OSS_ENDPOINT are required")

        try:
            import dashscope
            import oss2
            import requests
        except Exception as e:
            raise RuntimeError(f"deps missing (dashscope, oss2, requests): {e}")

        dashscope.api_key = dashscope_key
        auth_header = {"Authorization": f"Bearer {dashscope_key}"}
        auth = oss2.Auth(oss_access_key_id, oss_access_key_secret)
        bucket = oss2.Bucket(auth, oss_endpoint, oss_bucket_name)

        resp = dashscope.MultiModalConversation.call(
            model=tts_model,
            text=narration,
            voice=voice,
            language_type="Chinese",
        )
        if getattr(resp, "status_code", None) != 200:
            raise RuntimeError(f"TTS failed at page {slide_index}")
        audio_url = resp.output.audio["url"]
        raw = requests.get(audio_url, timeout=(10, 120)).content
        with open(audio_path, "wb") as f:
            f.write(raw)

        def _upload(local_path: str) -> str:
            ext = os.path.splitext(local_path)[1].lower() or ".bin"
            key = f"shuziren/{uuid.uuid4().hex}{ext}"
            bucket.put_object_from_file(key, local_path)
            return bucket.sign_url("GET", key, 7200)

        image_url = _upload(portrait_path)
        audio_file_url = _upload(audio_path)

        r = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/",
            headers={**auth_header, "Content-Type": "application/json", "X-DashScope-Async": "enable"},
            json={
                "model": video_model,
                "input": {"image_url": image_url, "audio_url": audio_file_url},
                "parameters": {"resolution": resolution},
            },
            timeout=30,
        )
        result = r.json()
        task_id = (result.get("output") or {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"submit task failed at page {slide_index}")

        start = time.time()
        while True:
            elapsed = int(time.time() - start)
            if elapsed > int(max_wait_seconds):
                raise TimeoutError(f"video task timeout at page {slide_index}")
            st = requests.get(f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}", headers=auth_header, timeout=15).json()
            status = (st.get("output") or {}).get("task_status") or "UNKNOWN"
            if status == "SUCCEEDED":
                results = (st.get("output") or {}).get("results") or {}
                video_url = results.get("video_url") if isinstance(results, dict) else None
                if not video_url:
                    raise RuntimeError(f"video_url missing at page {slide_index}")
                with requests.get(video_url, stream=True, timeout=(10, 600)) as rr:
                    with open(video_path, "wb") as f:
                        for chunk in rr.iter_content(8192):
                            if not chunk:
                                continue
                            f.write(chunk)
                return
            if status in {"FAILED", "CANCELED"}:
                raise RuntimeError(f"video task failed at page {slide_index}")
            time.sleep(10)
