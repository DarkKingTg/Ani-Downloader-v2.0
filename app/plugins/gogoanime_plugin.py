from __future__ import annotations

from typing import Any, Dict
import re

from app.plugins.base_plugin import BasePlugin
from app.plugins.generic_plugin import GenericPlugin


class GogoAnimePlugin(BasePlugin):
    SITE_NAME = "GogoAnime"
    URL_PATTERNS = [
        r"https?://(?:www\.)?(?:gogoanime|gogoanime\d+)\.(?:io|co|org|tv)/.+",
        r"https?://(?:www\.)?goload\.(?:io|pro|one)/.+",
    ]

    def extract_info(self, url: str) -> Dict[str, Any]:
        is_episode = "/episode-" in url or "-episode-" in url
        episode = None
        if is_episode:
            m = re.search(r"episode-(\d+)", url)
            episode = int(m.group(1)) if m else None
        return {
            "title": None,
            "episode": episode,
            "is_episode": is_episode,
            "webpage_url": url,
        }

    def download(self, url: str, output_path: str, **kwargs: Any) -> Dict[str, Any]:
        return GenericPlugin().download(url, output_path, **kwargs)

    def get_priority(self) -> int:
        return 80
