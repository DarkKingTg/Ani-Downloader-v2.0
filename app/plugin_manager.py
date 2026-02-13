"""
Common Logic File
Handles URL parsing and delegates tasks to the appropriate site plugin.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from typing import Any, Dict, List, Optional, Type

from app.plugins.base_plugin import BasePlugin
from app.plugins.generic_plugin import GenericPlugin


logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self) -> None:
        self.plugins: List[BasePlugin] = []
        self.fallback_plugin: BasePlugin = GenericPlugin()
        self._load_plugins()

    def _load_plugins(self) -> None:
        for m in pkgutil.iter_modules([__import__("app.plugins").plugins.__path__[0]]):
            module_name = m.name
            if module_name in {"base_plugin", "generic_plugin", "__init__"}:
                continue
            if not module_name.endswith("_plugin"):
                continue

            try:
                module = importlib.import_module(f"app.plugins.{module_name}")
            except Exception as e:
                logger.error("Failed to import plugin module %s: %s", module_name, e)
                continue

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if not issubclass(obj, BasePlugin) or obj is BasePlugin:
                    continue
                plugin_cls: Type[BasePlugin] = obj
                try:
                    plugin_instance = plugin_cls()
                except Exception as e:
                    logger.error("Failed to instantiate plugin %s: %s", plugin_cls.__name__, e)
                    continue

                if getattr(plugin_instance, "IS_FALLBACK", False):
                    self.fallback_plugin = plugin_instance
                else:
                    self.plugins.append(plugin_instance)

        self.plugins.sort(key=lambda p: p.get_priority(), reverse=True)

    def get_plugin_for_url(self, url: str) -> BasePlugin:
        for plugin in self.plugins:
            try:
                if plugin.can_handle(url):
                    return plugin
            except Exception:
                continue
        return self.fallback_plugin

    def download(self, url: str, output_path: str, **kwargs: Any) -> Dict[str, Any]:
        plugin = self.get_plugin_for_url(url)

        try:
            return plugin.download(url, output_path, **kwargs)
        except Exception as e:
            logger.error("Plugin %s failed: %s", getattr(plugin, "SITE_NAME", plugin.__class__.__name__), e)

            if getattr(plugin, "IS_FALLBACK", False):
                return {"success": False, "files": [], "error": str(e), "metadata": {}}

            try:
                return self.fallback_plugin.download(url, output_path, **kwargs)
            except Exception as fallback_error:
                return {"success": False, "files": [], "error": str(fallback_error), "metadata": {}}

    def extract_info(self, url: str) -> Dict[str, Any]:
        plugin = self.get_plugin_for_url(url)
        try:
            return plugin.extract_info(url)
        except Exception:
            try:
                return self.fallback_plugin.extract_info(url)
            except Exception:
                return {"error": "Failed to extract info"}

    def list_plugins(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for plugin in self.plugins:
            result.append(
                {
                    "name": plugin.SITE_NAME,
                    "priority": plugin.get_priority(),
                    "patterns": getattr(plugin, "URL_PATTERNS", []),
                }
            )
        if self.fallback_plugin:
            result.append(
                {
                    "name": getattr(self.fallback_plugin, "SITE_NAME", "Fallback"),
                    "priority": 0,
                    "patterns": ["*"],
                    "is_fallback": True,
                }
            )
        return result
