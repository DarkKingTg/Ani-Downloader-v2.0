"""
GogoAnime Plugin for Ani-Downloader
Example plugin for GogoAnime.is
"""

from app.plugin_system import AnimePlugin
from typing import List, Dict, Optional, Tuple, Any
import requests
import re
from bs4 import BeautifulSoup
import json

class GogoAnimePlugin(AnimePlugin):
    """Plugin for GogoAnime.is website"""

    @property
    def name(self) -> str:
        return "GogoAnime"

    @property
    def domain(self) -> str:
        return "gogoanime.is"  # Note: GogoAnime changes domains frequently

    @property
    def supports_search(self) -> bool:
        return True

    @property
    def supports_download(self) -> bool:
        return True

    def __init__(self):
        self.BASE_URL = "https://gogoanime.is"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search_anime(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search for anime on GogoAnime"""
        try:
            search_url = f"{self.BASE_URL}/search?keyword={query}"
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # GogoAnime search results
            anime_items = soup.select('.items li') or soup.select('.anime_list li')

            for item in anime_items[:max_results]:
                try:
                    link_elem = item.select_one('a')
                    img_elem = item.select_one('img')
                    title_elem = item.select_one('.name') or item.select_one('a')

                    if link_elem:
                        anime_url = link_elem.get('href', '')
                        if not anime_url.startswith('http'):
                            anime_url = f"{self.BASE_URL}{anime_url}"

                        anime_title = title_elem.get_text(strip=True) if title_elem else link_elem.get_text(strip=True)
                        anime_img = img_elem.get('src', '') if img_elem else ''

                        if anime_title and anime_url:
                            results.append({
                                'title': anime_title,
                                'url': anime_url,
                                'image': anime_img,
                                'anime_id': anime_url.split('/')[-1] if anime_url else '',
                                'source': self.domain
                            })
                except Exception as e:
                    continue

            return results
        except Exception as e:
            print(f"GogoAnime search error: {e}")
            return []

    def get_anime_details(self, url: str) -> Tuple[Optional[str], str]:
        """Get anime ID and title from URL"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract anime ID from URL
            anime_id = url.split('/')[-1] if '/' in url else None

            # Extract title
            title_elem = soup.select_one('.anime_info_body h1') or soup.select_one('.anime-title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            title = re.sub(r'[<>:"/\\|?*]', "", title)

            return anime_id, title
        except Exception as e:
            print(f"Error getting anime details: {e}")
            return None, "Unknown"

    def get_episode_list(self, anime_id: str) -> List[Dict[str, Any]]:
        """Get list of episodes for an anime"""
        try:
            anime_url = f"{self.BASE_URL}/category/{anime_id}"
            response = self.session.get(anime_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            episodes = []

            # Find episode list
            episode_items = soup.select('#episode_related li') or soup.select('.episode-list li')

            for item in episode_items:
                try:
                    link_elem = item.select_one('a')
                    if link_elem:
                        ep_url = link_elem.get('href', '')
                        if not ep_url.startswith('http'):
                            ep_url = f"{self.BASE_URL}{ep_url}"

                        # Extract episode number
                        ep_text = link_elem.get_text(strip=True)
                        ep_match = re.search(r'Episode\s*(\d+)', ep_text, re.IGNORECASE)
                        ep_id = ep_match.group(1) if ep_match else ep_text

                        episodes.append({
                            'id': ep_id,
                            'title': f'Episode {ep_id}',
                            'url': ep_url,
                            'token': ep_url
                        })
                except Exception as e:
                    continue

            return episodes
        except Exception as e:
            print(f"Error getting episode list: {e}")
            return []

    def get_video_servers(self, episode_token: str) -> List[Dict[str, Any]]:
        """Get available video servers for an episode"""
        try:
            response = self.session.get(episode_token, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            servers = []

            # Find video servers
            server_options = soup.select('.anime_muti_link ul li') or soup.select('.server-list li')

            for i, option in enumerate(server_options):
                try:
                    link_elem = option.select_one('a')
                    if link_elem:
                        server_name = link_elem.get_text(strip=True) or f"Server {i+1}"
                        server_url = link_elem.get('href', '')

                        servers.append({
                            'server_id': server_url,
                            'server_name': server_name,
                            'type': 'Sub',  # Assume sub by default
                            'quality': 'HD'  # Assume HD
                        })
                except Exception as e:
                    continue

            return servers
        except Exception as e:
            print(f"Error getting video servers: {e}")
            return []

    def get_video_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get video data from a server"""
        try:
            response = self.session.get(server_id, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for video URL in various places
            video_elem = soup.select_one('video source') or soup.select_one('iframe')
            if video_elem:
                if video_elem.name == 'source':
                    video_url = video_elem.get('src', '')
                else:
                    video_url = video_elem.get('src', '')

                if video_url and not video_url.startswith('http'):
                    video_url = f"https:{video_url}" if video_url.startswith('//') else video_url

                return {
                    'video_url': video_url,
                    'subtitles': [],
                    'quality': 'HD',
                    'format': 'mp4'
                }

            # If direct video not found, return the page URL for yt-dlp fallback
            return {
                'video_url': server_id,
                'subtitles': [],
                'quality': 'Unknown',
                'format': 'mp4',
                'use_ytdlp': True  # Flag to use yt-dlp
            }

        except Exception as e:
            print(f"Error getting video data: {e}")
            return None