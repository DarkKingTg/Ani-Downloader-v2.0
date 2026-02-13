from __future__ import annotations

import os
import sys
import time
import signal
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests


BASE_URL = os.environ.get("PLUGIN_TEST_BASE_URL", "http://127.0.0.1:5050")
SERVER_START_CMD = [sys.executable, os.path.join("scripts", "test_plugin_app.py")]

TEST_INFO_URL = os.environ.get("PLUGIN_TEST_INFO_URL", "https://gogoanime.io/one-piece-episode-1075")
TEST_DOWNLOAD_URL = os.environ.get("PLUGIN_TEST_DOWNLOAD_URL", "")
TEST_SERIES_URL = os.environ.get("PLUGIN_TEST_SERIES_URL", "https://gogoanime.io/category/one-piece")

ATTEMPTS_PER_FEATURE = int(os.environ.get("PLUGIN_TEST_ATTEMPTS", "5"))
TIMEOUT_SECONDS = float(os.environ.get("PLUGIN_TEST_TIMEOUT", "10"))


def _supports_ansi() -> bool:
    return sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    if not _supports_ansi():
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


def _bar(pct: float, width: int = 28) -> str:
    pct = max(0.0, min(100.0, pct))
    fill = int((pct / 100.0) * width)
    return "[" + ("#" * fill) + ("-" * (width - fill)) + "]"


@dataclass
class FeatureResult:
    name: str
    attempts: int = 0
    ok: int = 0
    errors: List[str] = field(default_factory=list)
    last_ms: Optional[float] = None

    def record(self, success: bool, elapsed_ms: float, error: Optional[str] = None) -> None:
        self.attempts += 1
        self.last_ms = elapsed_ms
        if success:
            self.ok += 1
        elif error:
            self.errors.append(error)

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return (self.ok / self.attempts) * 100.0

    @property
    def stability_label(self) -> str:
        r = self.success_rate
        if r >= 99:
            return "excellent"
        if r >= 90:
            return "good"
        if r >= 70:
            return "fair"
        return "unstable"


def _request(method: str, path: str, *, json_body: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, str]:
    url = BASE_URL.rstrip("/") + path
    t0 = time.perf_counter()
    try:
        r = requests.request(method, url, json=json_body, timeout=TIMEOUT_SECONDS)
        elapsed = (time.perf_counter() - t0) * 1000.0
        if 200 <= r.status_code < 300:
            return True, elapsed, ""
        snippet = r.text.strip()
        if len(snippet) > 240:
            snippet = snippet[:240] + "..."
        return False, elapsed, f"HTTP {r.status_code}: {snippet}"
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return False, elapsed, str(e)


def _is_server_alive() -> bool:
    ok, _, _ = _request("GET", "/health")
    return ok


def _start_server() -> Optional[subprocess.Popen]:
    if _is_server_alive():
        return None

    proc = subprocess.Popen(
        SERVER_START_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )

    deadline = time.time() + 12
    while time.time() < deadline:
        if _is_server_alive():
            return proc
        time.sleep(0.35)

    return proc


def _stop_server(proc: Optional[subprocess.Popen]) -> None:
    if not proc:
        return

    try:
        if os.name == "nt":
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            proc.terminate()
    except Exception:
        pass

    try:
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _print_header() -> None:
    print("=" * 70)
    print("Plugin System Test Runner (Terminal UI)")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print(f"Attempts per feature: {ATTEMPTS_PER_FEATURE}")
    print(f"Info URL: {TEST_INFO_URL}")
    print(f"Series URL: {TEST_SERIES_URL}")
    if TEST_DOWNLOAD_URL:
        print(f"Download URL: {TEST_DOWNLOAD_URL}")
    else:
        print("Download URL: (skipped; set PLUGIN_TEST_DOWNLOAD_URL to enable)")
    print("=" * 70)


def _line(result: FeatureResult) -> str:
    pct = result.success_rate
    ms = "-" if result.last_ms is None else f"{result.last_ms:.0f}ms"
    label = result.stability_label
    name = f"{result.name:<18}"

    bar = _bar(pct)
    pct_txt = f"{pct:6.1f}%"

    if pct >= 90:
        pct_txt = _c(pct_txt, "32")
    elif pct >= 70:
        pct_txt = _c(pct_txt, "33")
    else:
        pct_txt = _c(pct_txt, "31")

    return f"{name} {bar} {pct_txt}  ok {result.ok}/{result.attempts}  last {ms}  stability: {label}"


def main() -> int:
    _print_header()

    server_proc = _start_server()
    if not _is_server_alive():
        print(_c("Server failed to start or is unreachable.", "31"))
        if server_proc and server_proc.stdout:
            try:
                out = server_proc.stdout.read(2000)
                if out:
                    print("--- server output (tail) ---")
                    print(out)
            except Exception:
                pass
        _stop_server(server_proc)
        return 2

    print(_c("Server is running. Starting feature tests...", "36"))

    features: List[Tuple[FeatureResult, Callable[[], Tuple[bool, float, str]]]] = []

    health = FeatureResult("health")
    features.append((health, lambda: _request("GET", "/health")))

    plugins = FeatureResult("list_plugins")
    features.append((plugins, lambda: _request("GET", "/api/plugins")))

    info = FeatureResult("extract_info")
    features.append((info, lambda: _request("POST", "/api/info", json_body={"url": TEST_INFO_URL})))

    batch = FeatureResult("batch_download")
    features.append(
        (
            batch,
            lambda: _request(
                "POST",
                "/api/batch-download",
                json_body={"series_url": TEST_SERIES_URL, "episodes": [1, 2]},
            ),
        )
    )

    if TEST_DOWNLOAD_URL:
        download = FeatureResult("download")
        out_dir = os.path.join(os.getcwd(), "downloads", "plugin_test")
        features.append(
            (
                download,
                lambda: _request(
                    "POST",
                    "/api/download",
                    json_body={"url": TEST_DOWNLOAD_URL, "output_path": out_dir},
                ),
            )
        )

    total_steps = ATTEMPTS_PER_FEATURE * len(features)
    step = 0

    try:
        for _ in range(ATTEMPTS_PER_FEATURE):
            for result, fn in features:
                ok, ms, err = fn()
                result.record(ok, ms, None if ok else err)
                step += 1

                if _supports_ansi():
                    sys.stdout.write("\x1b[2J\x1b[H")
                    _print_header()
                    print(_c("Live progress:", "36"))
                else:
                    print("\n--- progress ---")

                overall_pct = (step / total_steps) * 100.0
                print(f"Overall: {_bar(overall_pct)} {overall_pct:5.1f}% ({step}/{total_steps})")
                print("-")
                for r, _ in features:
                    print(_line(r))
                time.sleep(0.15)

    finally:
        _stop_server(server_proc)

    print("\n" + "=" * 70)
    print("Final Report")
    print("=" * 70)

    overall_attempts = sum(r.attempts for r, _ in features)
    overall_ok = sum(r.ok for r, _ in features)
    overall_rate = (overall_ok / overall_attempts) * 100.0 if overall_attempts else 0.0

    print(f"Overall success rate: {overall_rate:.1f}% ({overall_ok}/{overall_attempts})")
    print("-")

    for r, _ in features:
        print(_line(r))
        if r.errors:
            uniq: List[str] = []
            for e in r.errors:
                if e not in uniq:
                    uniq.append(e)
                if len(uniq) >= 2:
                    break
            for e in uniq:
                print(f"  - last error: {e}")

    print("=")
    print("Notes:")
    print("- batch_download will likely be 0% until a plugin implements get_episode_list().")
    print("- download success depends on yt-dlp working for the chosen URL/environment.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
