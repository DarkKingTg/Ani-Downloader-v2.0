from __future__ import annotations

from typing import Any, Dict, List
import os
import subprocess
import glob

import yt_dlp

from app.plugins.base_plugin import BasePlugin


class GenericPlugin(BasePlugin):
    SITE_NAME = "Generic (yt-dlp + AniKai fallback)"
    URL_PATTERNS = [r".*"]
    IS_FALLBACK = True

    def can_handle(self, url: str) -> bool:
        return True

    def get_priority(self) -> int:
        return 0

    def extract_info(self, url: str) -> Dict[str, Any]:
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "webpage_url": info.get("webpage_url") or url,
                "extractor": info.get("extractor"),
            }
        except Exception:
            return {"title": None, "webpage_url": url}

    def download(self, url: str, output_path: str, **kwargs: Any) -> Dict[str, Any]:
        os.makedirs(output_path, exist_ok=True)

        outtmpl = os.path.join(output_path, "%(title)s-%(id)s.%(ext)s")
        fmt = kwargs.get("format") or "bestvideo+bestaudio/best"
        merge_format = kwargs.get("merge_output_format") or "mp4"

        quality = kwargs.get("quality")
        fps = kwargs.get("fps")

        constraints = []
        if quality and str(quality).strip().lower() not in {"", "best", "auto"}:
            quality_digits = "".join(ch for ch in str(quality) if ch.isdigit())
            if quality_digits:
                constraints.append(f"height<={int(quality_digits)}")
        if fps and str(fps).strip().lower() not in {"", "best", "auto"}:
            fps_digits = "".join(ch for ch in str(fps) if ch.isdigit())
            if fps_digits:
                constraints.append(f"fps<={int(fps_digits)}")

        if constraints:
            selector = "[" + "][".join(constraints) + "]"
            fmt = f"bestvideo{selector}+bestaudio/best{selector}/best"

        before_files = set(glob.glob(os.path.join(output_path, "*")))

        cmd = [
            "yt-dlp",
            "-o",
            outtmpl,
            "-f",
            fmt,
            "--merge-output-format",
            str(merge_format),
            url,
        ]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "yt-dlp failed").strip()
                return {"success": False, "files": [], "error": err, "metadata": {}}

            after_files = set(glob.glob(os.path.join(output_path, "*")))
            new_files = sorted(after_files - before_files)
            if not new_files:
                # Heuristic: pick latest modified file
                all_files = [p for p in after_files if os.path.isfile(p)]
                all_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                new_files = all_files[:1]

            return {"success": True, "files": new_files, "error": None, "metadata": {}}
        except Exception as e:
            return {"success": False, "files": [], "error": str(e), "metadata": {}}
