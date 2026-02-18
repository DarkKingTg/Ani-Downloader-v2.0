from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.downloader import AnimeDownloader
from app.plugins.base_plugin import BasePlugin
from app.plugins.generic_plugin import GenericPlugin


class AnimeKaiPlugin(BasePlugin):
    SITE_NAME = "AniKai.to"
    URL_PATTERNS = [
        r"^https?://(?:www\.)?anikai\.to/.*$",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._downloader = AnimeDownloader()
        self._generic = GenericPlugin()

    def get_priority(self) -> int:
        return 100

    def _parse_episode_from_url(self, url: str) -> Optional[str]:
        m = re.search(r"[?#&]ep=(\d+(?:\.\d+)?)", url)
        if m:
            return m.group(1)
        return None

    def _normalize_watch_url(self, url: str) -> str:
        parts = urlparse(url)
        return f"{parts.scheme}://{parts.netloc}{parts.path}"

    def _extract_expected_total_episodes_from_html(self, html: str) -> Optional[int]:
        patterns = [
            r"\bEpisodes\b\s*[:\-]?\s*(\d{1,4})",
            r"\bTotal\s+Episodes\b\s*[:\-]?\s*(\d{1,4})",
            r"\bep_end\b\s*[:=]\s*(\d{1,4})",
            r"\btotalEpisodes\b\s*[:=]\s*(\d{1,4})",
        ]
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE)
            if not m:
                continue
            try:
                return int(m.group(1))
            except Exception:
                continue
        return None

    def _discover_season_links(self, watch_url: str) -> List[Dict[str, str]]:
        """Best-effort season discovery.

        AniKai doesn't have a stable public "seasons" API in our core downloader,
        so we scrape the watch page and look for additional /watch/... links.
        """

        try:
            r = self._downloader.scraper.get(watch_url, headers=self._downloader.HEADERS, timeout=30)
            r.raise_for_status()
            html = r.text
        except Exception:
            return [{"url": watch_url, "name": "Season 1"}]

        soup = BeautifulSoup(html, "html.parser")

        # Try to prioritize links coming from season/related areas (class names are best-effort)
        candidate_containers = soup.select(
            ".seasons, .season, .season-list, .related, .related-anime, .anisc-related, .more-seasons"
        )
        if not candidate_containers:
            return [{"url": watch_url, "name": "Season 1"}]

        season_keywords = re.compile(r"\b(season|part|cour|s\d+)\b", re.IGNORECASE)

        seen: set[str] = set()
        seasons: List[Dict[str, str]] = []
        for container in candidate_containers:
            for a in container.select("a[href]"):
                href = a.get("href") or ""
                if "/watch/" not in href:
                    continue
                if href.startswith("//"):
                    href = "https:" + href
                if href.startswith("/"):
                    href = f"{urlparse(watch_url).scheme}://{urlparse(watch_url).netloc}{href}"
                if not href.startswith("http"):
                    continue

                normalized = self._normalize_watch_url(href)
                if normalized in seen:
                    continue
                seen.add(normalized)

                name = a.get_text(" ", strip=True) or ""
                if not name:
                    name = a.get("title") or ""

                # Avoid pulling unrelated shows: only accept links that look like seasons/parts.
                if name and not season_keywords.search(name):
                    continue

                seasons.append({"url": normalized, "name": name})

        # Always include current season first
        if watch_url not in seen:
            seasons.insert(0, {"url": watch_url, "name": ""})
        else:
            seasons = [{"url": watch_url, "name": ""}] + [s for s in seasons if s["url"] != watch_url]

        # Cap to avoid runaway scraping
        seasons = seasons[:6]

        # Fill in missing names with Season N
        for idx, s in enumerate(seasons, 1):
            if not s.get("name"):
                s["name"] = f"Season {idx}"

        return seasons

    def extract_info(self, url: str) -> Dict[str, Any]:
        watch_url = self._normalize_watch_url(url)
        anime_id, title = self._downloader.get_anime_details(watch_url)

        episode = self._parse_episode_from_url(url)

        total_episodes: Optional[int] = None
        expected_total_episodes: Optional[int] = None
        seasons: List[Dict[str, Any]] = []

        # Discover seasons (best-effort) and build full series structure.
        season_links = self._discover_season_links(watch_url)
        all_episode_urls_seen: set[str] = set()

        for idx, season in enumerate(season_links, 1):
            s_url = season.get("url") or watch_url
            s_name = season.get("name") or f"Season {idx}"

            s_anime_id, s_title = self._downloader.get_anime_details(s_url)
            if idx == 1 and (not title or title == "Unknown"):
                title = s_title
            if idx == 1 and (not anime_id):
                anime_id = s_anime_id

            episodes_payload: List[Dict[str, Any]] = []
            if s_anime_id:
                eps = self._downloader.get_episode_list(s_anime_id)
                for ep in eps:
                    ep_id = str(ep.get("id") or "").strip()
                    if not ep_id:
                        continue
                    ep_url = f"{s_url}#ep={ep_id}"
                    if ep_url in all_episode_urls_seen:
                        continue
                    all_episode_urls_seen.add(ep_url)
                    episodes_payload.append(
                        {
                            "episode": ep_id,
                            "title": ep.get("title") or f"Episode {ep_id}",
                            "subdub": ep.get("subdub") or "",
                            "url": ep_url,
                        }
                    )

            # best-effort expected total episodes from season page
            try:
                r = self._downloader.scraper.get(s_url, headers=self._downloader.HEADERS, timeout=30)
                if r.ok:
                    expected = self._extract_expected_total_episodes_from_html(r.text)
                    if expected is not None:
                        expected_total_episodes = max(expected_total_episodes or 0, expected)
            except Exception:
                pass

            seasons.append(
                {
                    "season_number": idx,
                    "season_name": s_name,
                    "webpage_url": s_url,
                    "episodes": episodes_payload,
                }
            )

        # total episodes is what we can actually enumerate
        total_episodes = sum(len(s.get("episodes") or []) for s in seasons)

        return {
            "title": title if title != "Unknown" else None,
            "episode": episode,
            "total_episodes": total_episodes,
            "expected_total_episodes": expected_total_episodes,
            "episodes": all_episode_urls_seen and [ep for s in seasons for ep in (s.get("episodes") or [])] or [],
            "seasons": seasons,
            "webpage_url": watch_url,
            "site": self.SITE_NAME,
        }

    def get_episode_list(self, series_url: str) -> List[Dict[str, Any]]:
        watch_url = self._normalize_watch_url(series_url)
        anime_id, _title = self._downloader.get_anime_details(watch_url)
        if not anime_id:
            return []

        eps = self._downloader.get_episode_list(anime_id)
        if not eps:
            return []

        result: List[Dict[str, Any]] = []
        for ep in eps:
            ep_id = str(ep.get("id") or "").strip()
            if not ep_id:
                continue

            try:
                ep_num: Any = int(float(ep_id))
            except Exception:
                ep_num = ep_id

            ep_url = f"{watch_url}#ep={ep_id}"
            result.append({"episode_number": ep_num, "url": ep_url})

        return result

    def download(self, url: str, output_path: str, **kwargs: Any) -> Dict[str, Any]:
        episode = self._parse_episode_from_url(url)
        if not episode:
            return self._generic.download(url, output_path, **kwargs)

        watch_url = self._normalize_watch_url(url)
        anime_id, title = self._downloader.get_anime_details(watch_url)
        if not anime_id:
            return {"success": False, "files": [], "error": "Failed to resolve anime id", "metadata": {}}

        episodes = self._downloader.get_episode_list(anime_id)
        target = None
        for ep in episodes:
            if str(ep.get("id")) == str(episode):
                target = ep
                break

        if not target:
            return {"success": False, "files": [], "error": f"Episode {episode} not found", "metadata": {}}

        token = target.get("token")
        if not token:
            return {"success": False, "files": [], "error": "Missing episode token", "metadata": {}}

        servers = self._downloader.get_video_servers(str(token))
        chosen = self._downloader.choose_server(
            servers,
            kwargs.get("prefer_type") or "Soft Sub",
            kwargs.get("prefer_server") or "",
        )
        if not chosen:
            return {"success": False, "files": [], "error": "No servers found", "metadata": {}}

        video_data = self._downloader.get_video_data(chosen.get("server_id", ""))
        if not video_data:
            return {"success": False, "files": [], "error": "Failed to fetch video data", "metadata": {}}

        os.makedirs(output_path, exist_ok=True)
        out_file = os.path.join(output_path, self._downloader.generate_episode_filename(title, 1, str(episode)))

        ok = self._downloader.download_episode(
            video_data,
            out_file,
            str(episode),
            quality=kwargs.get("quality"),
            fps=kwargs.get("fps"),
        )
        if not ok:
            return {"success": False, "files": [], "error": "Download failed", "metadata": {}}

        return {
            "success": True,
            "files": [out_file],
            "error": None,
            "metadata": {"title": title, "episode": episode, "site": self.SITE_NAME},
        }
