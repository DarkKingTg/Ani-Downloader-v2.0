from __future__ import annotations

from typing import Any, Dict

from app.plugins.base_plugin import BasePlugin
from app.plugins.generic_plugin import GenericPlugin


class NineAnimePlugin(BasePlugin):
    SITE_NAME = "9anime"
    URL_PATTERNS = [
        r"https?://(?:www\.)?9anime\.(?:to|pe|gg|tv)/.+",
    ]

    def extract_info(self, url: str) -> Dict[str, Any]:
        return {"title": None, "webpage_url": url}

    def download(self, url: str, output_path: str, **kwargs: Any) -> Dict[str, Any]:
        return GenericPlugin().download(url, output_path, **kwargs)

    def get_priority(self) -> int:
        return 82
