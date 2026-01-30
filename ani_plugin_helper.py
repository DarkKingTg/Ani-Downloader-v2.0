"""
Ani-Downloader Plugin Helper Library
====================================

A comprehensive utility library for creating Ani-Downloader plugins.
makes plugin development easy!

This library provides:
- Common web scraping utilities
- Anime site pattern helpers
- yt-dlp integration helpers
- Error handling and logging
- Base plugin templates
- Testing utilities

Author: Ani-Downloader Team
Version: 1.0.0
"""

import requests
import re
import json
import time
import logging
from typing import List, Dict, Optional, Tuple, Any, Union
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import yt_dlp
from functools import wraps
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginHelper:
    """Main helper class for plugin development"""

    def __init__(self, base_url: str, user_agent: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        # Set default headers
        default_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.session.headers.update({
            'User-Agent': user_agent or default_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        self.last_request_time = 0
        self.min_delay = 1.0  # Minimum delay between requests

    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make a rate-limited HTTP request"""
        # Ensure minimum delay between requests
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)

        try:
            self.last_request_time = time.time()
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Request failed: {url} - {e}")
            return None

    def get_soup(self, url: str, **kwargs) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup object from URL"""
        response = self.make_request(url, **kwargs)
        if response:
            return BeautifulSoup(response.text, 'html.parser')
        return None

    def extract_text(self, element, selectors: List[str], default: str = "") -> str:
        """Extract text using multiple selectors"""
        if not element:
            return default

        for selector in selectors:
            found = element.select_one(selector)
            if found:
                text = found.get_text(strip=True)
                if text:
                    return text
        return default

    def extract_attr(self, element, selectors: List[str], attr: str, default: str = "") -> str:
        """Extract attribute using multiple selectors"""
        if not element:
            return default

        for selector in selectors:
            found = element.select_one(selector)
            if found:
                value = found.get(attr, "")
                if value:
                    return value
        return default

class AnimeSiteHelper(PluginHelper):
    """Helper for common anime website patterns"""

    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url, **kwargs)
        self.anime_patterns = {
            'title': [
                'h1.title', '.anime-title', '.title',
                '.anime_name', '.series-title', 'h1'
            ],
            'description': [
                '.description', '.synopsis', '.summary',
                '.anime-description', '.plot'
            ],
            'image': [
                '.anime-image img', '.poster img', '.cover img',
                '.thumbnail img', 'img[src*="poster"]', 'img[src*="cover"]'
            ],
            'episodes': [
                '.episodes-count', '.total-episodes', '[data-episodes]',
                '.episode-count'
            ]
        }

    def extract_anime_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract common anime information from page"""
        info = {}

        # Title
        info['title'] = self.extract_text(soup, self.anime_patterns['title'])

        # Description
        info['description'] = self.extract_text(soup, self.anime_patterns['description'])

        # Image
        img_url = self.extract_attr(soup, self.anime_patterns['image'], 'src')
        if img_url and not img_url.startswith('http'):
            img_url = urljoin(self.base_url, img_url)
        info['image'] = img_url

        # Episodes
        episodes_text = self.extract_text(soup, self.anime_patterns['episodes'])
        episodes_match = re.search(r'(\d+)', episodes_text)
        info['episodes'] = int(episodes_match.group(1)) if episodes_match else None

        return info

    def find_anime_items(self, soup: BeautifulSoup, item_selectors: List[str]) -> List[Dict[str, Any]]:
        """Find anime items using multiple selectors"""
        for selector in item_selectors:
            items = soup.select(selector)
            if items:
                results = []
                for item in items:
                    anime_data = {
                        'title': self.extract_text(item, ['.title', '.name', 'a', 'h3']),
                        'url': self.extract_attr(item, ['a'], 'href'),
                        'image': self.extract_attr(item, ['img'], 'src'),
                    }

                    # Clean up URL
                    if anime_data['url'] and not anime_data['url'].startswith('http'):
                        anime_data['url'] = urljoin(self.base_url, anime_data['url'])

                    # Clean up image
                    if anime_data['image'] and not anime_data['image'].startswith('http'):
                        anime_data['image'] = urljoin(self.base_url, anime_data['image'])

                    if anime_data['title'] and anime_data['url']:
                        results.append(anime_data)

                return results
        return []

class YtDlpHelper:
    """Helper for yt-dlp integration"""

    @staticmethod
    def extract_info(url: str) -> Optional[Dict[str, Any]]:
        """Extract video information using yt-dlp"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count'),
                    'upload_date': info.get('upload_date'),
                    'formats': info.get('formats', []),
                    'best_format': YtDlpHelper.get_best_format(info.get('formats', [])),
                }
        except Exception as e:
            logger.error(f"yt-dlp extraction failed: {e}")
            return None

    @staticmethod
    def get_best_format(formats: List[Dict]) -> Optional[Dict]:
        """Get the best quality format"""
        if not formats:
            return None

        # Sort by quality (height, then bitrate)
        formats.sort(key=lambda x: (
            x.get('height', 0) or 0,
            x.get('tbr', 0) or 0
        ), reverse=True)

        return formats[0]

    @staticmethod
    def get_video_url(url: str) -> Optional[str]:
        """Get direct video URL for download"""
        info = YtDlpHelper.extract_info(url)
        if info and info.get('best_format'):
            return info['best_format'].get('url')
        return None

class PluginTemplate:
    """Template class for creating plugins quickly"""

    def __init__(self, name: str, domain: str, base_url: str):
        self.name = name
        self.domain = domain
        self.base_url = base_url
        self.helper = AnimeSiteHelper(base_url)

    def create_basic_plugin(self):
        """Generate a basic plugin structure"""
        template = f'''
from ani_plugin_helper import AnimeSiteHelper
from app.plugin_system import AnimePlugin
from typing import List, Dict, Optional, Tuple, Any

class {self.name.replace(" ", "")}Plugin(AnimePlugin):
    """Plugin for {self.domain}"""

    @property
    def name(self) -> str:
        return "{self.name}"

    @property
    def domain(self) -> str:
        return "{self.domain}"

    @property
    def supports_search(self) -> bool:
        return True

    @property
    def supports_download(self) -> bool:
        return True

    def __init__(self):
        self.helper = AnimeSiteHelper("{self.base_url}")

    def search_anime(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search for anime"""
        search_url = f"{self.base_url}/search?keyword={{query}}"
        soup = self.helper.get_soup(search_url.format(query=query))

        if not soup:
            return []

        # Customize these selectors for your site
        anime_items = self.helper.find_anime_items(soup, [
            '.anime-list .item',
            '.search-results .anime-item',
            '.results .anime'
        ])

        return anime_items[:max_results]

    def get_anime_details(self, url: str) -> Tuple[Optional[str], str]:
        """Get anime ID and title from URL"""
        soup = self.helper.get_soup(url)
        if not soup:
            return None, "Unknown"

        # Extract anime ID from URL
        anime_id = url.split('/')[-1] if '/' in url else None

        # Extract title
        info = self.helper.extract_anime_info(soup)
        title = info.get('title', 'Unknown')

        return anime_id, title

    def get_episode_list(self, anime_id: str) -> List[Dict[str, Any]]:
        """Get list of episodes"""
        # Implement episode list extraction
        # This will vary greatly between sites
        return []

    def get_video_servers(self, episode_token: str) -> List[Dict[str, Any]]:
        """Get available video servers"""
        # Implement server extraction
        return []

    def get_video_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get video data from server"""
        # Implement video URL extraction
        return None
'''
        return template

class PluginTester:
    """Testing utilities for plugin development"""

    def __init__(self, plugin_class):
        self.plugin_class = plugin_class
        self.plugin = None

    def initialize_plugin(self):
        """Initialize the plugin for testing"""
        try:
            self.plugin = self.plugin_class()
            return True
        except Exception as e:
            print(f"Plugin initialization failed: {e}")
            return False

    def test_search(self, query: str = "naruto"):
        """Test search functionality"""
        if not self.plugin:
            return False

        try:
            results = self.plugin.search_anime(query, 5)
            print(f"Search results for '{query}': {len(results)} found")
            if results:
                print(f"First result: {results[0]}")
            return True
        except Exception as e:
            print(f"Search test failed: {e}")
            return False

    def test_anime_details(self, test_url: str = None):
        """Test anime details extraction"""
        if not self.plugin or not test_url:
            return False

        try:
            anime_id, title = self.plugin.get_anime_details(test_url)
            print(f"Anime details - ID: {anime_id}, Title: {title}")
            return True
        except Exception as e:
            print(f"Anime details test failed: {e}")
            return False

    def run_basic_tests(self):
        """Run basic plugin tests"""
        print(f"Testing plugin: {self.plugin_class.__name__}")

        # Test initialization
        if not self.initialize_plugin():
            return False

        # Test search
        if not self.test_search():
            return False

        print("Basic tests passed!")
        return True

# Utility functions
def safe_filename(filename: str) -> str:
    """Create a safe filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def extract_number(text: str) -> Optional[int]:
    """Extract first number from text"""
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else None

def clean_html(text: str) -> str:
    """Clean HTML tags from text"""
    return re.sub(r'<[^>]+>', '', text).strip()

def setup_logging(level: str = 'INFO'):
    """Setup logging for plugin development"""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Export main classes
__all__ = [
    'PluginHelper',
    'AnimeSiteHelper',
    'YtDlpHelper',
    'PluginTemplate',
    'PluginTester',
    'safe_filename',
    'extract_number',
    'clean_html',
    'setup_logging'
]