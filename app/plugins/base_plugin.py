from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import re


class BasePlugin(ABC):
    URL_PATTERNS: List[str] = []
    SITE_NAME: str = "Unknown"

    def __init__(self) -> None:
        self._compiled_patterns = [re.compile(p) for p in self.URL_PATTERNS]

    def can_handle(self, url: str) -> bool:
        return any(p.match(url) for p in self._compiled_patterns)

    def get_priority(self) -> int:
        return 50

    @abstractmethod
    def extract_info(self, url: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def download(self, url: str, output_path: str, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError

    def get_episode_list(self, series_url: str) -> List[Dict[str, Any]]:
        return []


class PluginError(RuntimeError):
    pass


class UnsupportedUrlError(PluginError):
    pass
