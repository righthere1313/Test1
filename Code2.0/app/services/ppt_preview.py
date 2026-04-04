import json
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from pptx import Presentation


@dataclass(frozen=True)
class PPTPreviewOptions:
    width: int = 1600
    include_thumbnails: bool = True
    thumb_width: int = 320
    image_format: str = "png"


class PPTPreviewService:
    def __init__(self, *, root_dir: str) -> None:
        self.root_dir = str(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)

    def create_preview_id(self) -> str:
        return f"pv_{uuid.uuid4().hex}"

    def preview_dir(self, preview_id: str) -> str:
        return os.path.join(self.root_dir, preview_id)

    def meta_path(self, preview_id: str) -> str:
        return os.path.join(self.preview_dir(preview_id), "meta.json")

    def pages_dir(self, preview_id: str) -> str:
        return os.path.join(self.preview_dir(preview_id), "pages")

    def thumbs_dir(self, preview_id: str) -> str:
        return os.path.join(self.preview_dir(preview_id), "thumbs")

    def pdf_path(self, preview_id: str) -> str:
        return os.path.join(self.preview_dir(preview_id), "source.pdf")

    def is_valid_preview_id(self, preview_id: str) -> bool:
        return bool(re.fullmatch(r"pv_[0-9a-f]{32}", preview_id or ""))

    def get_slide_count(self, pptx_path: str) -> int:
        prs = Presentation(pptx_path)
        return len(list(prs.slides))

    def init_meta(self, *, preview_id: str, filename: str, total_pages: int, options: PPTPreviewOptions) -> dict:
        now = int(time.time())
        meta = {
            "preview_id": preview_id,
            "filename": filename,
            "status": "queued",
            "total_pages": int(total_pages),
            "progress": {"done_pages": 0, "total_pages": int(total_pages)},
            "options": {
                "width": int(options.width),
                "include_thumbnails": bool(options.include_thumbnails),
                "thumb_width": int(options.thumb_width),
                "format": str(options.image_format),
            },
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        self._write_meta(preview_id, meta)
        return meta

    def load_meta(self, preview_id: str) -> dict | None:
        p = self.meta_path(preview_id)
        if not os.path.exists(p):
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    def update_meta(self, preview_id: str, patch: dict) -> dict | None:
        meta = self.load_meta(preview_id) or {}
        if not isinstance(meta, dict):
            meta = {}
        for k, v in (patch or {}).items():
            meta[k] = v
        meta["updated_at"] = int(time.time())
        self._write_meta(preview_id, meta)
        return meta

    def _write_meta(self, preview_id: str, meta: dict) -> None:
        d = self.preview_dir(preview_id)
        os.makedirs(d, exist_ok=True)
        tmp = os.path.join(d, f".meta.{uuid.uuid4().hex}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
        os.replace(tmp, self.meta_path(preview_id))

    def run(self, *, preview_id: str, pptx_path: str, options: PPTPreviewOptions) -> None:
        pages_out = self.pages_dir(preview_id)
        thumbs_out = self.thumbs_dir(preview_id)
        pdf_out = self.pdf_path(preview_id)
        profile_dir = os.path.join(self.preview_dir(preview_id), f"lo_profile_{uuid.uuid4().hex}")

        os.makedirs(pages_out, exist_ok=True)
        if options.include_thumbnails:
            os.makedirs(thumbs_out, exist_ok=True)

        self.update_meta(preview_id, {"status": "processing"})

        try:
            self._convert_pptx_to_pdf(pptx_path=pptx_path, pdf_out=pdf_out, profile_dir=profile_dir)
            total_pages_pdf = self._pdf_page_count(pdf_out)
            meta = self.load_meta(preview_id) or {}
            total_pages = int(meta.get("total_pages") or 0) or int(total_pages_pdf)
            self.update_meta(preview_id, {"total_pages": total_pages, "progress": {"done_pages": 0, "total_pages": total_pages}})

            self._convert_pdf_to_pngs(pdf_path=pdf_out, out_dir=pages_out, width=options.width)
            done = self._count_pages(pages_out)
            self.update_meta(preview_id, {"progress": {"done_pages": done, "total_pages": total_pages}})

            if options.include_thumbnails:
                self._convert_pdf_to_pngs(pdf_path=pdf_out, out_dir=thumbs_out, width=options.thumb_width)

            self.update_meta(preview_id, {"status": "done", "progress": {"done_pages": total_pages, "total_pages": total_pages}})
        except Exception as e:
            self.update_meta(preview_id, {"status": "failed", "error": {"code": "RENDER_FAILED", "message": str(e)}})
        finally:
            try:
                shutil.rmtree(profile_dir, ignore_errors=True)
            except Exception:
                pass

    def _convert_pptx_to_pdf(self, *, pptx_path: str, pdf_out: str, profile_dir: str) -> None:
        out_dir = os.path.dirname(pdf_out)
        os.makedirs(out_dir, exist_ok=True)
        src = Path(pptx_path).resolve()
        if not src.exists():
            raise FileNotFoundError("pptx not found")

        os.makedirs(profile_dir, exist_ok=True)
        cmd = [
            "soffice",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "-env:UserInstallation=file://" + str(Path(profile_dir).resolve()),
            "--convert-to",
            "pdf",
            str(src),
            "--outdir",
            str(Path(out_dir).resolve()),
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "soffice failed")

        expected = os.path.join(out_dir, f"{src.stem}.pdf")
        if not os.path.exists(expected):
            raise RuntimeError("pdf not generated")
        if os.path.abspath(expected) != os.path.abspath(pdf_out):
            os.replace(expected, pdf_out)

    def _pdf_page_count(self, pdf_path: str) -> int:
        cmd = ["pdfinfo", str(Path(pdf_path).resolve())]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "pdfinfo failed")
        for line in (proc.stdout or "").splitlines():
            if line.lower().startswith("pages:"):
                raw = line.split(":", 1)[1].strip()
                try:
                    return int(raw)
                except Exception:
                    break
        raise RuntimeError("cannot parse pdf pages")

    def _convert_pdf_to_pngs(self, *, pdf_path: str, out_dir: str, width: int) -> None:
        os.makedirs(out_dir, exist_ok=True)
        out_prefix = os.path.join(out_dir, "page")
        cmd = [
            "pdftocairo",
            "-png",
            "-scale-to",
            str(int(width)),
            str(Path(pdf_path).resolve()),
            str(Path(out_prefix).resolve()),
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "pdftocairo failed")

    def _count_pages(self, out_dir: str) -> int:
        try:
            names = os.listdir(out_dir)
        except Exception:
            return 0
        count = 0
        for n in names:
            if re.fullmatch(r"page-\d+\.png", n):
                count += 1
        return count

    def _find_image_file(self, out_dir: str, page: int) -> str | None:
        try:
            names = os.listdir(out_dir)
        except Exception:
            return None
        
        patterns = [
            f"page-{int(page):02d}.png",
            f"page-{int(page):01d}.png",
            f"page-{int(page):03d}.png"
        ]
        
        for pattern in patterns:
            if pattern in names:
                return os.path.join(out_dir, pattern)
        
        for name in names:
            m = re.fullmatch(r"page-0*(\d+)\.png", name)
            if m and m.group(1) == str(int(page)):
                return os.path.join(out_dir, name)
        
        return None

    def page_image_path(self, preview_id: str, page: int) -> str:
        pages_dir = self.pages_dir(preview_id)
        found = self._find_image_file(pages_dir, page)
        if found:
            return found
        return os.path.join(pages_dir, f"page-{int(page)}.png")

    def thumb_image_path(self, preview_id: str, page: int) -> str:
        thumbs_dir = self.thumbs_dir(preview_id)
        found = self._find_image_file(thumbs_dir, page)
        if found:
            return found
        return os.path.join(thumbs_dir, f"page-{int(page)}.png")

    def delete_preview(self, preview_id: str) -> None:
        d = self.preview_dir(preview_id)
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
