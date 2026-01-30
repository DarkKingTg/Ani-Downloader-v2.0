"""
AnimeKai Plugin for Ani-Downloader
Original AnimeKai.to support extracted into a plugin
"""

from app.plugin_system import AnimePlugin
from typing import List, Dict, Optional, Tuple, Any
import cloudscraper
import re
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse

class AnimeKaiPlugin(AnimePlugin):
    """Plugin for AnimeKai.to website"""

    @property
    def name(self) -> str:
        return "AnimeKai"

    @property
    def domain(self) -> str:
        return "anikai.to"

    @property
    def supports_search(self) -> bool:
        return True

    @property
    def supports_download(self) -> bool:
        return True

    def __init__(self):
        self.BASE_URL = "https://anikai.to"
        self.scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True}
        )
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.BASE_URL,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }

    def search_anime(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search for anime on AnimeKai"""
        try:
            search_url = f"{self.BASE_URL}/browser?keyword={query}"

            response = self.scraper.get(search_url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # Try multiple possible selectors
            anime_items = (
                soup.select('.anime-item') or
                soup.select('.film_list-wrap .flw-item') or
                soup.select('.block_area-content .item') or
                soup.select('article') or
                soup.select('.anime-card') or
                soup.select('[class*="anime"]') or
                soup.select('[class*="item"]')
            )

            seen_urls = set()

            for item in anime_items[:max_results * 2]:  # Check more items to account for duplicates
                try:
                    # Try multiple selector patterns
                    link_elem = (
                        item.select_one('a[href*="/watch/"]') or
                        item.select_one('a[href*="/anime/"]') or
                        item.select_one('a.film-poster-ahref') or
                        item.select_one('.film-name a') or
                        item.select_one('a')
                    )

                    title_elem = (
                        item.select_one('.film-name') or
                        item.select_one('.title') or
                        item.select_one('h3') or
                        item.select_one('.anime-name') or
                        item.select_one('[class*="title"]')
                    )

                    img_elem = item.select_one('img')

                    if link_elem:
                        anime_url = link_elem.get('href', '')
                        if not anime_url.startswith('http'):
                            anime_url = f"{self.BASE_URL}{anime_url}"

                        # Skip duplicates
                        if anime_url in seen_urls:
                            continue

                        seen_urls.add(anime_url)

                        anime_title = title_elem.get_text(strip=True) if title_elem else link_elem.get_text(strip=True)
                        anime_img = img_elem.get('src', '') or img_elem.get('data-src', '') if img_elem else ''

                        if anime_title and anime_url:
                            results.append({
                                'title': anime_title,
                                'url': anime_url,
                                'image': anime_img,
                                'anime_id': anime_url.split('/')[-1] if anime_url else '',
                                'source': self.domain
                            })

                            # Stop once we have enough unique results
                            if len(results) >= max_results:
                                break
                except Exception as e:
                    continue

            return results
        except Exception as e:
            print(f"AnimeKai search error: {e}")
            return []

    def get_anime_details(self, url: str) -> Tuple[Optional[str], str]:
        """Get anime ID and title from URL"""
        try:
            r = self.scraper.get(url, headers=self.HEADERS, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            anime_div = soup.select_one("div[data-id]")
            anime_id = anime_div.get("data-id") if anime_div else None

            title_elem = (
                soup.select_one("div.title-wrapper h1.title span")
                or soup.select_one("h1.title")
                or soup.select_one(".anime-title")
            )
            title = title_elem.get("title") if title_elem and title_elem.get("title") else (
                title_elem.text.strip() if title_elem else "Unknown"
            )
            title = re.sub(r'[<>:"/\\|?*]', "", title)
            return anime_id, title
        except Exception as e:
            print(f"Error getting anime details: {e}")
            return None, "Unknown"

    def get_episode_list(self, anime_id: str) -> List[Dict[str, Any]]:
        """Get list of episodes for an anime"""
        try:
            # This would need to be implemented based on AnimeKai's API
            # For now, return empty list as this requires specific AnimeKai logic
            return []
        except Exception as e:
            return []

    def get_video_servers(self, episode_token: str) -> List[Dict[str, Any]]:
        """Get available video servers for an episode"""
        try:
            # This would need to be implemented based on AnimeKai's API
            return []
        except Exception as e:
            return []

    def get_video_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get video data from a server"""
        try:
            # This would need to be implemented based on AnimeKai's API
            return None
        except Exception as e:
            return None