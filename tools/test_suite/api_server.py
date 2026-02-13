from __future__ import annotations

import os
from typing import Any, Dict, List

from flask import Flask, jsonify, request

from app.plugin_manager import PluginManager


def _json_error(message: str, status_code: int = 400, *, details: Any = None):
    payload: Dict[str, Any] = {"success": False, "error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code


def create_test_app() -> Flask:
    app = Flask(__name__)

    plugin_manager = PluginManager()

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/api/plugins")
    def list_plugins():
        return jsonify({"success": True, "plugins": plugin_manager.list_plugins()})

    @app.post("/api/info")
    def extract_info():
        data = request.get_json(silent=True) or {}
        url = data.get("url")
        if not url:
            return _json_error("url is required", 400)

        info = plugin_manager.extract_info(url)
        return jsonify({"success": True, "info": info})

    @app.post("/api/download")
    def download_single():
        data = request.get_json(silent=True) or {}
        url = data.get("url")
        if not url:
            return _json_error("url is required", 400)

        download_folder = data.get("output_path") or os.path.join(os.getcwd(), "downloads")
        quality = data.get("quality")
        fmt = data.get("format")

        result = plugin_manager.download(url, download_folder, quality=quality, format=fmt)
        status = 200 if result.get("success") else 500
        return jsonify(result), status

    @app.post("/api/batch-download")
    def batch_download():
        data = request.get_json(silent=True) or {}
        series_url = data.get("series_url")
        if not series_url:
            return _json_error("series_url is required", 400)

        download_folder = data.get("output_path") or os.path.join(os.getcwd(), "downloads")
        quality = data.get("quality")
        fmt = data.get("format")

        plugin = plugin_manager.get_plugin_for_url(series_url)
        episode_list: List[Dict[str, Any]] = []
        try:
            episode_list = plugin.get_episode_list(series_url)
        except Exception:
            episode_list = []

        if not episode_list:
            return _json_error(
                "Plugin does not support episode listing for this series_url (or returned empty list)",
                501,
                details={"plugin": getattr(plugin, "SITE_NAME", plugin.__class__.__name__)},
            )

        requested = data.get("episodes")
        if requested:
            requested_set = set(int(x) for x in requested)
            episode_list = [
                ep for ep in episode_list if int(ep.get("episode_number")) in requested_set
            ]

        results: List[Dict[str, Any]] = []
        for ep in episode_list:
            ep_url = ep.get("url")
            ep_num = ep.get("episode_number")
            if not ep_url:
                results.append({"episode": ep_num, "success": False, "error": "missing url"})
                continue

            r = plugin_manager.download(ep_url, download_folder, quality=quality, format=fmt)
            results.append(
                {
                    "episode": ep_num,
                    "success": bool(r.get("success")),
                    "files": r.get("files", []),
                    "error": r.get("error"),
                }
            )

        return jsonify({"success": True, "results": results})

    @app.errorhandler(404)
    def not_found(_e):
        return _json_error("not found", 404)

    @app.errorhandler(500)
    def internal_error(e):
        return _json_error("internal server error", 500, details=str(e))

    return app


def main() -> None:
    app = create_test_app()
    app.run(debug=True, host="127.0.0.1", port=5050)


if __name__ == "__main__":
    main()
