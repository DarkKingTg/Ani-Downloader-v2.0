# Plugin Authoring Guide

This project supports site-specific plugins under `app/plugins/`.

## 1) Create a new plugin file

Use the naming convention:

- `app/plugins/<site>_plugin.py`

Example: `app/plugins/example_plugin.py`

## 2) Implement the plugin class

Your class must inherit `BasePlugin` from `app/plugins/base_plugin.py` and implement:

- `extract_info(url)`
- `download(url, output_path, **kwargs)`

Optional methods:

- `get_priority()` (higher = selected first)
- `get_episode_list(series_url)` for batch download features

## 3) Required class attributes

Define at minimum:

- `SITE_NAME` (human readable name)
- `URL_PATTERNS` (regex list used for routing)

Example skeleton:

```python
from __future__ import annotations
from typing import Any, Dict
from app.plugins.base_plugin import BasePlugin

class ExamplePlugin(BasePlugin):
    SITE_NAME = "ExampleSite"
    URL_PATTERNS = [r"^https?://(?:www\.)?example\.com/.*$"]

    def get_priority(self) -> int:
        return 80

    def extract_info(self, url: str) -> Dict[str, Any]:
        return {"title": None, "webpage_url": url}

    def download(self, url: str, output_path: str, **kwargs: Any) -> Dict[str, Any]:
        return {"success": False, "files": [], "error": "Not implemented", "metadata": {}}
```

## 4) Download return contract

`download(...)` must return:

```json
{
  "success": true|false,
  "files": ["/abs/or/relative/path"],
  "error": "nullable error text",
  "metadata": {"optional": "details"}
}
```

## 5) Quality/FPS support

If possible, honor optional kwargs:

- `quality`
- `fps`
- `prefer_type`
- `prefer_server`

These are already propagated by the main download flow.

## 6) Fallback behavior

If your plugin cannot handle a URL in practice, return a structured failure or defer to your own fallback strategy. The global `PluginManager` also has fallback behavior.

## 7) Validate your plugin

Recommended checks:

1. `python -m compileall app run.py`
2. run plugin API tests via `scripts/test_plugin_runner.py`
3. verify selection order using the plugin list endpoint

## 8) Common pitfalls

- Don’t swallow exceptions silently; return/log actionable errors.
- Keep URL regex strict enough to avoid hijacking unrelated domains.
- Ensure downloaded files are actually created before returning success.
