"""
Plugin System for Ani-Downloader
Allows extending the application to support multiple anime websites
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any
import os
import importlib.util
import inspect

class AnimePlugin(ABC):
    """Base class for anime website plugins"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass

    @property
    @abstractmethod
    def domain(self) -> str:
        """Website domain (e.g., 'anikai.to')"""
        pass

    @property
    @abstractmethod
    def supports_search(self) -> bool:
        """Whether this plugin supports search functionality"""
        pass

    @property
    @abstractmethod
    def supports_download(self) -> bool:
        """Whether this plugin supports downloading"""
        pass

    @abstractmethod
    def search_anime(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for anime on this website
        Returns list of anime with keys: title, url, image, anime_id, etc.
        """
        pass

    @abstractmethod
    def get_anime_details(self, url: str) -> Tuple[Optional[str], str]:
        """
        Get anime ID and title from URL
        Returns (anime_id, title)
        """
        pass

    @abstractmethod
    def get_episode_list(self, anime_id: str) -> List[Dict[str, Any]]:
        """
        Get list of episodes for an anime
        Returns list of episodes with keys: id, title, url, etc.
        """
        pass

    @abstractmethod
    def get_video_servers(self, episode_token: str) -> List[Dict[str, Any]]:
        """
        Get available video servers for an episode
        Returns list of servers with keys: server_id, server_name, type, etc.
        """
        pass

    @abstractmethod
    def get_video_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video data from a server
        Returns dict with keys: video_url, subtitles, etc.
        """
        pass

    def choose_server(self, servers: List[Dict[str, Any]], prefer_type: str = "Soft Sub",
                      prefer_server: str = "Server 1") -> Optional[Dict[str, Any]]:
        """
        Choose the best server from available options
        Default implementation - can be overridden
        """
        if not servers:
            return None

        # Filter by preferred type
        type_filtered = [s for s in servers if s.get('type', '').lower() == prefer_type.lower()]
        if not type_filtered:
            type_filtered = servers

        # Find preferred server
        for server in type_filtered:
            if prefer_server.lower() in server.get('server_name', '').lower():
                return server

        # Return first available
        return type_filtered[0]

    def generate_episode_filename(self, anime_title: str, season: int, episode_id: str) -> str:
        """
        Generate filename for episode
        Default implementation - can be overridden
        """
        safe_title = "".join(c for c in anime_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if season and season > 0:
            return f"{safe_title} S{season:02d}E{episode_id}.mp4"
        else:
            return f"{safe_title} Episode {episode_id}.mp4"

    def detect_season_from_title(self, title: str) -> int:
        """
        Detect season number from anime title
        Default implementation - can be overridden
        """
        import re
        # Look for season patterns
        patterns = [
            r'Season\s*(\d+)',
            r'S(\d+)',
            r'(\d+)\w*\s*Season',
        ]
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 1

    def safe_episode_key(self, episode_id: str) -> str:
        """
        Convert episode ID to sortable key
        Default implementation - can be overridden
        """
        import re
        # Extract numbers and pad them
        parts = re.split(r'(\d+)', episode_id)
        return ''.join(part.zfill(4) if part.isdigit() else part for part in parts)


class PluginManager:
    """Manages loading and using plugins"""

    def __init__(self, plugins_dir: str = None):
        if plugins_dir is None:
            # Default to plugins directory in the parent directory (same level as app/)
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            plugins_dir = os.path.join(current_dir, 'plugins')

        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, AnimePlugin] = {}
        self._load_plugins()

    def _load_plugins(self):
        """Load all plugins from the plugins directory"""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
            return

        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_path = os.path.join(self.plugins_dir, filename)
                try:
                    self._load_plugin(plugin_path)
                except Exception as e:
                    print(f"Failed to load plugin {filename}: {e}")

    def _load_plugin(self, plugin_path: str):
        """Load a single plugin file"""
        module_name = os.path.splitext(os.path.basename(plugin_path))[0]

        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {plugin_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find plugin classes
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                issubclass(obj, AnimePlugin) and
                obj != AnimePlugin):
                plugin_instance = obj()
                self.plugins[plugin_instance.domain] = plugin_instance
                print(f"Loaded plugin: {plugin_instance.name} ({plugin_instance.domain})")

    def get_plugin_for_url(self, url: str) -> Optional[AnimePlugin]:
        """Get the appropriate plugin for a URL"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]

        # First try exact domain match
        plugin = self.plugins.get(domain)
        if plugin:
            return plugin

        # If no exact match, try the generic plugin as fallback
        generic_plugin = self.plugins.get('generic')
        if generic_plugin:
            return generic_plugin

        return None

    def get_available_plugins(self) -> List[AnimePlugin]:
        """Get list of all loaded plugins"""
        return list(self.plugins.values())

    def search_all_plugins(self, query: str, max_results: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all plugins that support search"""
        results = {}
        for domain, plugin in self.plugins.items():
            if plugin.supports_search:
                try:
                    plugin_results = plugin.search_anime(query, max_results)
                    if plugin_results:
                        results[domain] = plugin_results
                except Exception as e:
                    print(f"Search failed for {domain}: {e}")
        return results