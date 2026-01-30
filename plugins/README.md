# Ani-Downloader Plugin System

The Ani-Downloader now supports a plugin system that allows developers to add support for additional anime websites beyond the default AnimeKai.to.

## 🛠️ Helper Library

Plugin development is made easy with the `ani_plugin_helper.py` library, which provides:

- **AnimeSiteHelper**: Common anime website patterns and utilities
- **YtDlpHelper**: yt-dlp integration helpers
- **PluginTemplate**: Quick plugin scaffolding
- **PluginTester**: Testing utilities

See the [Plugin Development Tutorial](../PLUGIN_DEVELOPMENT_TUTORIAL.md) for detailed usage.

## How It Works

The plugin system uses yt-dlp as the core download engine, which supports hundreds of websites. Plugins provide the website-specific logic for:

- Searching for anime
- Extracting episode lists
- Resolving video URLs
- Handling website-specific encoding/decoding

## Creating a Plugin

1. Create a new Python file in the `plugins/` directory
2. Inherit from `AnimePlugin` base class
3. Implement the required abstract methods
4. The plugin will be automatically loaded on startup

## Plugin Base Class

```python
from app.plugin_system import AnimePlugin

class MyAnimePlugin(AnimePlugin):
    @property
    def name(self) -> str:
        return "My Anime Site"

    @property
    def domain(self) -> str:
        return "myanimesite.com"

    @property
    def supports_search(self) -> bool:
        return True  # Set to False if only direct URL downloads

    @property
    def supports_download(self) -> bool:
        return True

    def search_anime(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        # Implement search logic
        # Return list of dicts with: title, url, image, anime_id, source
        pass

    def get_anime_details(self, url: str) -> Tuple[Optional[str], str]:
        # Extract anime ID and title from URL
        # Return (anime_id, title)
        pass

    def get_episode_list(self, anime_id: str) -> List[Dict[str, Any]]:
        # Get list of episodes
        # Return list of dicts with: id, title, url, token
        pass

    def get_video_servers(self, episode_token: str) -> List[Dict[str, Any]]:
        # Get available video servers
        # Return list of dicts with: server_id, server_name, type, quality
        pass

    def get_video_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        # Get video URL and subtitles
        # Return dict with: video_url, subtitles, quality, format
        # If yt-dlp fallback needed, set 'use_ytdlp': True
        pass
```

## Example Plugins

### AnimeKai Plugin (`plugins/anikai.py`)
- Full implementation for AnimeKai.to
- Handles proprietary encoding/decoding
- Supports search and download

### yt-dlp Generic Plugin (`plugins/ytdlp_generic.py`)
- Supports any yt-dlp compatible website
- No search functionality (direct URLs only)
- Automatic video extraction

### GogoAnime Plugin (`plugins/gogoanime.py`)
- Example implementation for GogoAnime.is
- Demonstrates web scraping approach
- Fallback to yt-dlp for video extraction

### Example Plugin (`plugins/example_plugin.py`)
- **NEW!** Comprehensive example showing best practices
- Uses the helper library extensively
- Includes detailed comments and error handling
- Perfect starting point for new plugin development
- Demonstrates all plugin methods with real-world patterns

## Using Plugins

### Automatic Detection
The system automatically detects which plugin to use based on the URL domain:

```python
# Will use AnimeKai plugin
url = "https://anikai.to/watch/naruto-123"

# Will use yt-dlp generic plugin for any supported site
url = "https://youtube.com/watch?v=..."
url = "https://crunchyroll.com/..."
```

### Manual Plugin Selection
For search, you can specify a plugin:

```javascript
// Search using specific plugin
fetch('/api/search/anime?q=naruto&plugin=gogoanime')
```

### Getting Available Plugins
```javascript
fetch('/api/search/plugins')
  .then(r => r.json())
  .then(data => console.log(data.plugins));
```

## Plugin Development Tips

1. **Error Handling**: Always wrap operations in try-catch blocks
2. **User Agents**: Use appropriate headers to avoid blocking
3. **Rate Limiting**: Implement delays between requests
4. **Fallbacks**: Use yt-dlp as fallback when direct extraction fails
5. **Testing**: Test with various anime titles and edge cases

## Supported Websites

Since the system uses yt-dlp, it supports any website that yt-dlp supports, including:

- YouTube
- Crunchyroll
- Funimation
- Netflix (with cookies)
- And hundreds more...

## Contributing

To contribute a new plugin:

1. Fork the repository
2. Create your plugin in `plugins/your_plugin.py`
3. Test thoroughly
4. Submit a pull request

Please include:
- Plugin name and description
- Supported websites
- Any special setup requirements
- Example usage