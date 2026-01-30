"""
Example Plugin: Basic Anime Site Support
=========================================

This is an example plugin showing how to use the ani_plugin_helper library
to create plugins for Ani-Downloader. This plugin demonstrates:

- Using AnimeSiteHelper for common patterns
- Basic web scraping techniques
- Error handling
- Plugin structure

To use this as a template:
1. Copy this file to plugins/your_plugin.py
2. Replace the URLs and selectors with your target site
3. Test thoroughly
4. Submit as a contribution!

Author: Ani-Downloader Community
"""

from app.plugin_system import AnimePlugin
from ani_plugin_helper import AnimeSiteHelper, YtDlpHelper, safe_filename
from typing import List, Dict, Optional, Tuple, Any
import re
import logging

logger = logging.getLogger(__name__)

class ExampleAnimePlugin(AnimePlugin):
    """
    Example plugin for a fictional anime site: anime-example.com

    This plugin demonstrates best practices for plugin development:
    - Using the helper library
    - Proper error handling
    - Logging
    - Clean code structure
    """

    @property
    def name(self) -> str:
        return "Example Anime Site"

    @property
    def domain(self) -> str:
        return "anime-example.com"

    @property
    def supports_search(self) -> bool:
        return True

    @property
    def supports_download(self) -> bool:
        return True

    def __init__(self):
        # Initialize helper with base URL
        self.helper = AnimeSiteHelper("https://anime-example.com")
        logger.info(f"Initialized {self.name} plugin")

    def search_anime(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for anime using the helper library

        Args:
            query: Search term
            max_results: Maximum number of results to return

        Returns:
            List of anime dictionaries with title, url, image
        """
        try:
            logger.info(f"Searching for: {query}")

            # Construct search URL
            search_url = f"https://anime-example.com/search?keyword={query}"

            # Get page content using helper
            soup = self.helper.get_soup(search_url)
            if not soup:
                logger.error("Failed to load search page")
                return []

            # Define selectors for this site (customize for your site)
            anime_selectors = [
                '.anime-list .item',      # Common pattern
                '.search-results .anime', # Alternative pattern
                '.results .anime-item'    # Another common pattern
            ]

            # Use helper to find anime items
            anime_items = self.helper.find_anime_items(soup, anime_selectors)

            # Filter and clean results
            results = []
            for item in anime_items[:max_results]:
                # Validate required fields
                if item.get('title') and item.get('url'):
                    # Ensure URL is absolute
                    if not item['url'].startswith('http'):
                        item['url'] = f"https://anime-example.com{item['url']}"

                    # Clean title
                    item['title'] = item['title'].strip()

                    results.append(item)

            logger.info(f"Found {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

    def get_anime_details(self, url: str) -> Tuple[Optional[str], str]:
        """
        Extract anime ID and title from URL

        Args:
            url: Anime page URL

        Returns:
            Tuple of (anime_id, title) or (None, "Unknown") on failure
        """
        try:
            logger.info(f"Getting details for: {url}")

            # Load anime page
            soup = self.helper.get_soup(url)
            if not soup:
                return None, "Failed to load page"

            # Extract anime info using helper
            info = self.helper.extract_anime_info(soup)

            # Extract anime ID from URL
            # Example: https://anime-example.com/anime/naruto-shippuden
            anime_id_match = re.search(r'/anime/([^/?]+)', url)
            anime_id = anime_id_match.group(1) if anime_id_match else None

            title = info.get('title', 'Unknown')

            logger.info(f"Extracted anime: {anime_id} - {title}")
            return anime_id, title

        except Exception as e:
            logger.error(f"Failed to get anime details for {url}: {e}")
            return None, "Unknown"

    def get_episode_list(self, anime_id: str) -> List[Dict[str, Any]]:
        """
        Get list of episodes for an anime

        Args:
            anime_id: Internal anime identifier

        Returns:
            List of episode dictionaries
        """
        try:
            logger.info(f"Getting episodes for anime: {anime_id}")

            # Construct anime page URL
            anime_url = f"https://anime-example.com/anime/{anime_id}"

            soup = self.helper.get_soup(anime_url)
            if not soup:
                return []

            episodes = []

            # Find episode links (customize selectors for your site)
            episode_selectors = [
                '.episode-list a',
                '.episodes a',
                '.episode-links a'
            ]

            for selector in episode_selectors:
                episode_links = soup.select(selector)
                if episode_links:
                    break

            for link in episode_links:
                episode_title = link.get_text(strip=True)
                episode_url = link.get('href')

                if episode_url and episode_title:
                    # Extract episode number
                    ep_match = re.search(r'episode-(\d+)', episode_url)
                    ep_num = int(ep_match.group(1)) if ep_match else len(episodes) + 1

                    # Ensure absolute URL
                    if not episode_url.startswith('http'):
                        episode_url = f"https://anime-example.com{episode_url}"

                    episodes.append({
                        'episode_number': ep_num,
                        'title': episode_title,
                        'url': episode_url
                    })

            # Sort by episode number
            episodes.sort(key=lambda x: x['episode_number'])

            logger.info(f"Found {len(episodes)} episodes")
            return episodes

        except Exception as e:
            logger.error(f"Failed to get episodes for {anime_id}: {e}")
            return []

    def get_video_servers(self, episode_token: str) -> List[Dict[str, Any]]:
        """
        Get available video servers for an episode

        Args:
            episode_token: Episode URL or identifier

        Returns:
            List of server dictionaries
        """
        try:
            logger.info(f"Getting servers for episode: {episode_token}")

            soup = self.helper.get_soup(episode_token)
            if not soup:
                return []

            servers = []

            # Find server options (customize for your site)
            server_selectors = [
                '.server-list option',
                '.servers option',
                '.video-servers option'
            ]

            for selector in server_selectors:
                server_options = soup.select(selector)
                if server_options:
                    break

            for i, option in enumerate(server_options):
                server_name = option.get_text(strip=True)
                server_value = option.get('value')

                if server_name and server_value:
                    servers.append({
                        'id': f"server_{i}",
                        'name': server_name,
                        'value': server_value
                    })

            # If no servers found, assume direct video
            if not servers:
                servers.append({
                    'id': 'direct',
                    'name': 'Direct',
                    'value': episode_token
                })

            logger.info(f"Found {len(servers)} servers")
            return servers

        except Exception as e:
            logger.error(f"Failed to get servers for {episode_token}: {e}")
            return []

    def get_video_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract video download information

        Args:
            server_id: Server identifier

        Returns:
            Video data dictionary or None
        """
        try:
            logger.info(f"Getting video data for server: {server_id}")

            # For this example, we'll use yt-dlp as fallback
            # In a real plugin, you'd extract the actual video URL

            # Try to extract video URL from page
            soup = self.helper.get_soup(server_id)
            if soup:
                # Look for video elements
                video_selectors = [
                    'video source',
                    '.video-player source',
                    '.player video source'
                ]

                for selector in video_selectors:
                    video_elem = soup.select_one(selector)
                    if video_elem:
                        video_url = video_elem.get('src')
                        if video_url:
                            return {
                                'url': video_url if video_url.startswith('http') else f"https://anime-example.com{video_url}",
                                'format': 'mp4',
                                'quality': '720p'
                            }

                # Look for iframe embeds
                iframe = soup.select_one('.video-player iframe, .player iframe')
                if iframe:
                    iframe_src = iframe.get('src')
                    if iframe_src and 'youtube.com' in iframe_src:
                        # Use yt-dlp for YouTube embeds
                        return YtDlpHelper.extract_info(iframe_src)

            # Fallback to yt-dlp if direct extraction fails
            logger.info("Falling back to yt-dlp extraction")
            return YtDlpHelper.extract_info(server_id)

        except Exception as e:
            logger.error(f"Failed to get video data for {server_id}: {e}")
            return None

# Plugin metadata for the plugin registry
PLUGIN_METADATA = {
    "name": "Example Anime Plugin",
    "version": "1.0.0",
    "author": "Ani-Downloader Community",
    "description": "Example plugin demonstrating best practices",
    "supported_sites": ["anime-example.com"],
    "requires": ["beautifulsoup4", "requests"],
    "tags": ["example", "tutorial", "template"]
}

if __name__ == "__main__":
    # Quick test when run directly
    from ani_plugin_helper import PluginTester

    print("Testing Example Anime Plugin...")
    tester = PluginTester(ExampleAnimePlugin)

    if tester.initialize_plugin():
        print("✓ Plugin initialized successfully")

        # Test with a sample query
        results = tester.test_search("naruto")
        if results:
            print("✓ Search test passed")
        else:
            print("✗ Search test failed")

        print("Plugin test complete!")
    else:
        print("✗ Plugin initialization failed")