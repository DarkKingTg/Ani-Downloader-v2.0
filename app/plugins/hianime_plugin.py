from __future__ import annotations

from typing import Any, Dict
import re

from app.plugins.base_plugin import BasePlugin
from app.plugins.generic_plugin import GenericPlugin


class HiAnimePlugin(BasePlugin):
    SITE_NAME = "HiAnime (Aniwatch)"
    URL_PATTERNS = [
        r"https?://(?:www\.)?(?:hianime|aniwatch)\.(?:to|tv)/.+",
    ]

    def extract_info(self, url: str) -> Dict[str, Any]:
        episode_id = None
        m = re.search(r"[?&]ep=(\d+)", url)
        if m:
            episode_id = m.group(1)
        return {
            "title": None,
            "episode": episode_id,
            "webpage_url": url,
        }

    def download(self, url: str, output_path: str, **kwargs: Any) -> Dict[str, Any]:
        return GenericPlugin().download(url, output_path, **kwargs)

    def get_priority(self) -> int:
        return 85
