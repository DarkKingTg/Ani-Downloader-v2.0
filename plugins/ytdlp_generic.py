"""
Generic yt-dlp Plugin for Ani-Downloader
Supports any website that yt-dlp can handle with direct URLs
"""

from app.plugin_system import AnimePlugin
from typing import List, Dict, Optional, Tuple, Any
import yt_dlp
import re
from urllib.parse import urlparse

class YtDlpPlugin(AnimePlugin):
    """Generic plugin using yt-dlp for any supported website"""

    @property
    def name(self) -> str:
        return "yt-dlp Generic"

    @property
    def domain(self) -> str:
        return "generic"  # This plugin handles any domain yt-dlp supports

    @property
    def supports_search(self) -> bool:
        return False  # This plugin doesn't support search, only direct URL downloads

    @property
    def supports_download(self) -> bool:
        return True

    def search_anime(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """This plugin doesn't support search"""
        return []

    def get_anime_details(self, url: str) -> Tuple[Optional[str], str]:
        """Extract basic info from URL"""
        try:
            # Try to extract title from yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    title = info.get('title', 'Unknown')
                    # Use URL as ID
                    anime_id = url
                    return anime_id, title
        except Exception as e:
            print(f"yt-dlp info extraction failed: {e}")

        # Fallback: extract from URL
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        title = path_parts[-1] if path_parts else 'Unknown'
        title = re.sub(r'[<>:"/\\|?*]', "", title)
        return url, title

    def get_episode_list(self, anime_id: str) -> List[Dict[str, Any]]:
        """For direct URLs, treat as single episode"""
        return [{
            'id': '1',
            'title': 'Video',
            'url': anime_id,
            'token': anime_id
        }]

    def get_video_servers(self, episode_token: str) -> List[Dict[str, Any]]:
        """Return single server for yt-dlp"""
        return [{
            'server_id': episode_token,
            'server_name': 'yt-dlp Direct',
            'type': 'Direct',
            'quality': 'Best Available'
        }]

    def get_video_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get video data using yt-dlp"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(server_id, download=False)
                if info:
                    # Get best video URL
                    formats = info.get('formats', [])
                    if formats:
                        # Sort by quality (prefer higher resolution)
                        formats.sort(key=lambda x: (
                            x.get('height', 0) or 0,
                            x.get('tbr', 0) or 0
                        ), reverse=True)

                        best_format = formats[0]
                        video_url = best_format.get('url')

                        if video_url:
                            return {
                                'video_url': video_url,
                                'subtitles': [],  # yt-dlp could extract subtitles if available
                                'quality': f"{best_format.get('height', 'Unknown')}p",
                                'format': best_format.get('ext', 'mp4')
                            }
        except Exception as e:
            print(f"yt-dlp video data extraction failed: {e}")

        return None

    def choose_server(self, servers: List[Dict[str, Any]], prefer_type: str = "Direct",
                      prefer_server: str = "yt-dlp Direct") -> Optional[Dict[str, Any]]:
        """Choose the yt-dlp server"""
        return servers[0] if servers else None