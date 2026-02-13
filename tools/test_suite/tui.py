#!/usr/bin/env python3
"""Terminal UI Test Application for Anime Downloader Plugin System."""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict, Optional

from app.plugin_manager import PluginManager


def _optional_imports():
    try:
        from colorama import Fore, Style, init  # type: ignore

        init(autoreset=True)
    except Exception:
        Fore = None  # type: ignore
        Style = None  # type: ignore

    try:
        import questionary  # type: ignore
        from questionary import Style as QStyle  # type: ignore

        custom_style = QStyle(
            [
                ("qmark", "fg:#673ab7 bold"),
                ("question", "bold"),
                ("answer", "fg:#f44336 bold"),
                ("pointer", "fg:#673ab7 bold"),
                ("highlighted", "fg:#673ab7 bold"),
                ("selected", "fg:#cc5454"),
                ("separator", "fg:#cc5454"),
                ("instruction", ""),
                ("text", ""),
            ]
        )
    except Exception:
        questionary = None  # type: ignore
        custom_style = None  # type: ignore

    return Fore, Style, questionary, custom_style


Fore, Style, questionary, custom_style = _optional_imports()


class AnimeDownloaderTestApp:
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.test_results = []

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self):
        self.clear_screen()
        if Fore and Style:
            print(f"{Fore.CYAN}{'='*60}")
            print(f"{Fore.CYAN}  ANIME DOWNLOADER - TEST SUITE")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        else:
            print("=" * 60)
            print("  ANIME DOWNLOADER - TEST SUITE")
            print("=" * 60 + "\n")

    def _warn_missing_deps(self):
        if questionary is None or Fore is None:
            print("Interactive UI dependencies are missing.")
            print("Install them for the full terminal UI experience:")
            print("  pip install questionary colorama")
            print("\nContinuing with basic text prompts...\n")
            input("Press Enter to continue...")

    def main_menu(self):
        self._warn_missing_deps()

        while True:
            self.print_header()

            if questionary:
                choice = questionary.select(
                    "Select an option:",
                    choices=[
                        "Self Test - System Health Check",
                        "Test Download - Test URL Download",
                        "Plugin Status - View Loaded Plugins",
                        "Quick Test - Run Predefined Tests",
                        "View Results - Show Previous Test Results",
                        "Exit",
                    ],
                    style=custom_style,
                ).ask()
            else:
                print("1) Self Test - System Health Check")
                print("2) Test Download - Test URL Download")
                print("3) Plugin Status - View Loaded Plugins")
                print("4) Quick Test - Run Predefined Tests")
                print("5) View Results - Show Previous Test Results")
                print("6) Exit")
                choice = input("Select option: ").strip()

            if not choice or "Exit" in choice or choice == "6":
                print("\nGoodbye!")
                sys.exit(0)
            if "Self Test" in choice or choice == "1":
                self.self_test()
            elif "Test Download" in choice or choice == "2":
                self.test_download()
            elif "Plugin Status" in choice or choice == "3":
                self.plugin_status()
            elif "Quick Test" in choice or choice == "4":
                self.quick_test()
            elif "View Results" in choice or choice == "5":
                self.view_results()

    def self_test(self):
        self.print_header()
        print("Running Self Test...\n")

        tests = []

        print("[1/5] Testing plugin loading...", end="")
        plugins = self.plugin_manager.list_plugins()
        if len(plugins) > 0:
            print(f" PASS ({len(plugins)} plugins loaded)")
            tests.append(True)
        else:
            print(" FAIL (No plugins loaded)")
            tests.append(False)

        print("[2/5] Checking fallback plugin...", end="")
        fallback = [p for p in plugins if p.get("is_fallback")]
        if fallback:
            print(f" PASS ({fallback[0].get('name')})")
            tests.append(True)
        else:
            print(" FAIL (No fallback plugin)")
            tests.append(False)

        print("[3/5] Checking yt-dlp (python import)...", end="")
        try:
            import yt_dlp  # noqa: F401

            print(" PASS")
            tests.append(True)
        except Exception:
            print(" FAIL (yt_dlp import failed)")
            tests.append(False)

        print("[4/5] Checking download directory...", end="")
        download_dir = "./test_downloads"
        os.makedirs(download_dir, exist_ok=True)
        if os.path.exists(download_dir) and os.access(download_dir, os.W_OK):
            print(f" PASS ({download_dir})")
            tests.append(True)
        else:
            print(f" FAIL (Cannot write to {download_dir})")
            tests.append(False)

        print("[5/5] Testing URL pattern matching...", end="")
        test_urls = {
            "https://gogoanime.io/test-episode-1": "gogo",
            "https://hianime.to/watch/test": "hianime",
            "https://example.com/video": "generic",
        }
        matched = 0
        for url, expected in test_urls.items():
            plugin = self.plugin_manager.get_plugin_for_url(url)
            if expected in plugin.SITE_NAME.lower():
                matched += 1

        if matched == len(test_urls):
            print(f" PASS ({matched}/{len(test_urls)} matched)")
            tests.append(True)
        else:
            print(f" PARTIAL ({matched}/{len(test_urls)} matched)")
            tests.append(False)

        passed = sum(1 for t in tests if t)
        total = len(tests)
        print("\n" + ("=" * 60))
        print(f"Result: {passed}/{total} passed")
        print(("=" * 60))
        input("Press Enter to return to menu...")

    def test_download(self):
        self.print_header()

        if questionary:
            mode = questionary.select(
                "Select test mode:",
                choices=["Auto (Use predefined test URLs)", "Custom (Enter your own URL)"],
                style=custom_style,
            ).ask()
        else:
            mode = input("Mode (auto/custom): ").strip().lower()
            mode = "Auto" if mode.startswith("a") else "Custom"

        if not mode:
            return

        if "Auto" in mode:
            self._auto_test_download()
        else:
            self._custom_test_download()

    def _auto_test_download(self):
        test_urls = [
            "https://gogoanime.io/one-piece-episode-1075",
            "https://hianime.to/watch/jujutsu-kaisen-534?ep=1234",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ]

        print(f"\nRunning auto tests with {len(test_urls)} URLs...\n")
        for idx, url in enumerate(test_urls, 1):
            print(f"Test {idx}/{len(test_urls)}: {url}")
            self._run_test(url, auto=True)
            print()

        input("Press Enter to return to menu...")

    def _custom_test_download(self):
        print("\nCustom Test Mode\n")

        if questionary:
            url = questionary.text(
                "Enter anime URL:",
                validate=lambda x: len(x) > 0 or "URL cannot be empty",
            ).ask()
        else:
            url = input("Enter anime URL: ").strip()

        if not url:
            return

        info = self.plugin_manager.extract_info(url)
        plugin = self.plugin_manager.get_plugin_for_url(url)

        print("\nDetected Information:")
        print(f"  - Website: {plugin.SITE_NAME}")
        print(f"  - Title: {info.get('title', 'Unknown')}")
        if info.get("episode"):
            print(f"  - Episode: {info.get('episode')}")

        if questionary:
            download_type = questionary.select(
                "What do you want to do?",
                choices=[
                    "Single Episode (This URL only)",
                    "Just test info extraction (No download)",
                ],
                style=custom_style,
            ).ask()
        else:
            download_type = input("Action (download/info): ").strip().lower()
            download_type = "Just test" if download_type.startswith("i") else "Single"

        if not download_type:
            return

        if "Just test" in download_type:
            self._display_info_only(url, info, plugin)
            input("\nPress Enter to return to menu...")
            return

        if questionary:
            quality = questionary.select(
                "Select quality:",
                choices=["1080", "720", "480", "360", "best"],
                style=custom_style,
            ).ask()
        else:
            quality = input("Quality (1080/720/480/360/best): ").strip() or "best"

        if questionary:
            fmt = questionary.select(
                "Select format:",
                choices=["bestvideo+bestaudio/best", "best"],
                style=custom_style,
            ).ask()
        else:
            fmt = input("Format (default bestvideo+bestaudio/best): ").strip() or "bestvideo+bestaudio/best"

        dry_run = True
        if questionary:
            dry_run = questionary.confirm("Dry run (no download)?", default=True).ask()
        else:
            dry_run = (input("Dry run? (y/n): ").strip().lower() or "y") in {"y", "yes"}

        cfg = {"quality": quality, "format": fmt, "dry_run": dry_run}
        self._run_test(url, auto=False, config=cfg)
        input("\nPress Enter to return to menu...")

    def _run_test(self, url: str, auto: bool = False, config: Optional[Dict[str, Any]] = None):
        start_time = time.time()

        plugin = self.plugin_manager.get_plugin_for_url(url)
        info = self.plugin_manager.extract_info(url)

        print(f"Plugin: {plugin.SITE_NAME}")
        print(f"URL: {url}")

        if auto:
            for k, v in info.items():
                if v and k != "error":
                    print(f"  - {k}: {v}")

            result = {
                "website": plugin.SITE_NAME,
                "anime_name": info.get("title", "Unknown"),
                "episode": info.get("episode"),
                "status": "Info extracted (auto test - no download)",
            }
        else:
            config = config or {}
            dry_run = bool(config.get("dry_run", True))
            out_dir = "./test_downloads"
            os.makedirs(out_dir, exist_ok=True)

            print("\nConfiguration:")
            print(f"  - Quality: {config.get('quality', 'best')}")
            print(f"  - Format: {config.get('format', 'bestvideo+bestaudio/best')}")
            print(f"  - Output: {out_dir}")
            print(f"  - Dry run: {dry_run}")

            if dry_run:
                result = {
                    "website": plugin.SITE_NAME,
                    "anime_name": info.get("title", "Unknown"),
                    "episode": info.get("episode"),
                    "status": "Simulated (dry run)",
                    "config": config,
                }
            else:
                dl = self.plugin_manager.download(
                    url,
                    out_dir,
                    quality=None if config.get("quality") in {"best", None} else config.get("quality"),
                    format=config.get("format"),
                )

                result = {
                    "website": plugin.SITE_NAME,
                    "anime_name": info.get("title", "Unknown"),
                    "episode": info.get("episode"),
                    "status": "Success" if dl.get("success") else "Failed",
                    "download": dl,
                    "config": config,
                }

        elapsed = time.time() - start_time
        print("\n" + ("=" * 60))
        print("TEST RESULTS")
        print(("=" * 60))
        print(f"Website: {result.get('website')}")
        print(f"Anime Name: {result.get('anime_name')}")
        print(f"Episode: {result.get('episode', 'N/A')}")
        print(f"Status: {result.get('status')}")
        print(f"Time Elapsed: {elapsed:.2f}s")
        if result.get("download"):
            print(f"Download Success: {result['download'].get('success')}")
            if result["download"].get("error"):
                print(f"Download Error: {result['download'].get('error')}")
        print(("=" * 60))

        self.test_results.append(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "url": url,
                "result": result,
            }
        )

    def _display_info_only(self, url: str, info: Dict[str, Any], plugin: Any):
        print("\n" + ("=" * 60))
        print("EXTRACTED INFORMATION")
        print(("=" * 60))
        print(f"Website: {plugin.SITE_NAME}")
        print(f"Title: {info.get('title', 'Unknown')}")
        print(f"Episode: {info.get('episode', 'N/A')}")
        if info.get("total_episodes") is not None:
            print(f"Total Episodes: {info.get('total_episodes')}")
        if info.get("expected_total_episodes") is not None:
            print(f"Expected Total Episodes: {info.get('expected_total_episodes')}")

        seasons = info.get("seasons") or []
        if isinstance(seasons, list) and seasons:
            print("\nSeasons:")
            for s in seasons:
                s_num = s.get("season_number")
                s_name = s.get("season_name") or (f"Season {s_num}" if s_num else "Season")
                eps = s.get("episodes") or []
                try:
                    eps_count = len(eps) if isinstance(eps, list) else 0
                except Exception:
                    eps_count = 0
                print(f"  - {s_name} ({eps_count} episodes)")

            # show a small preview list of episode URLs
            first_season = seasons[0]
            eps_preview = first_season.get("episodes") or []
            if isinstance(eps_preview, list) and eps_preview:
                print("\nEpisodes (preview):")
                for ep in eps_preview[:10]:
                    ep_no = ep.get("episode") or ep.get("episode_number") or "?"
                    ep_title = ep.get("title") or ""
                    ep_url = ep.get("url") or ""
                    line = f"  - EP {ep_no}"
                    if ep_title:
                        line += f": {ep_title}"
                    if ep_url:
                        line += f" | {ep_url}"
                    print(line)
                if len(eps_preview) > 10:
                    print(f"  ... and {len(eps_preview) - 10} more")

        print(f"URL: {url}")
        print(("=" * 60))

    def plugin_status(self):
        self.print_header()

        plugins = self.plugin_manager.list_plugins()
        print(f"Loaded Plugins: {len(plugins)}\n")

        for idx, p in enumerate(plugins, 1):
            is_fallback = p.get("is_fallback", False)
            print(f"{idx}. {p.get('name')}")
            print(f"   Priority: {p.get('priority')}")
            print(f"   Type: {'Fallback' if is_fallback else 'Site-specific'}")
            patterns = p.get("patterns") or []
            if is_fallback:
                print("   Patterns: Matches all URLs")
            else:
                print(f"   Patterns: {len(patterns)}")
            print()

        input("Press Enter to return to menu...")

    def quick_test(self):
        self.print_header()

        print("Quick Test Suite\n")
        test_cases = [
            ("GogoAnime", "https://gogoanime.io/naruto-episode-220"),
            ("HiAnime", "https://hianime.to/watch/one-piece-100?ep=12345"),
            ("9anime", "https://9anime.to/watch/attack-on-titan.123/ep-75"),
            ("Generic", "https://example.com/some-video"),
        ]

        passed = 0
        for expected, url in test_cases:
            plugin = self.plugin_manager.get_plugin_for_url(url)
            matched = expected.lower() in plugin.SITE_NAME.lower()
            passed += 1 if matched else 0
            print(f"{'PASS' if matched else 'FAIL'} {expected}: {url}")
            print(f"  Matched to: {plugin.SITE_NAME}\n")

        print(f"Results: {passed}/{len(test_cases)} passed")
        input("\nPress Enter to return to menu...")

    def view_results(self):
        self.print_header()

        if not self.test_results:
            print("No test results available yet.\n")
            input("Press Enter to return to menu...")
            return

        print(f"Previous Test Results ({len(self.test_results)})\n")
        for idx, test in enumerate(self.test_results, 1):
            status = test["result"].get("status", "Unknown")
            print(f"{idx}. {test['timestamp']}")
            print(f"   URL: {test['url']}")
            print(f"   Status: {status}\n")

        input("Press Enter to return to menu...")


def main() -> None:
    app = AnimeDownloaderTestApp()

    try:
        app.main_menu()
    except KeyboardInterrupt:
        print("\nTest application terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
