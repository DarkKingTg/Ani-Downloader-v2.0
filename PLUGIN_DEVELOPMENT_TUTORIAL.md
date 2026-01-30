# Ani-Downloader Plugin Development Tutorial

## Table of Contents
1. [Introduction](#introduction)
2. [Setting Up Development Environment](#setting-up-development-environment)
3. [Understanding Plugin Architecture](#understanding-plugin-architecture)
4. [Creating Your First Plugin](#creating-your-first-plugin)
5. [Using the Helper Library](#using-the-helper-library)
6. [Advanced Plugin Features](#advanced-plugin-features)
7. [Testing Your Plugin](#testing-your-plugin)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Publishing Your Plugin](#publishing-your-plugin)
11. [Updating the Application](#updating-the-application)

## Introduction

Welcome to the Ani-Downloader Plugin Development Tutorial! This guide will teach you how to create plugins for Ani-Downloader, allowing users to download anime from any website.

### What are Plugins?
Plugins extend Ani-Downloader's functionality to support new anime websites. Each plugin handles:
- Searching for anime
- Extracting episode lists
- Getting video download links
- Handling site-specific logic

### Why Create Plugins?
- Support your favorite anime sites
- Contribute to the community
- Learn web scraping and plugin development
- Customize download behavior

## Setting Up Development Environment

### Prerequisites
- Python 3.8+
- Git
- Basic knowledge of HTML/CSS
- Understanding of web scraping concepts

### Clone the Repository
```bash
git clone https://github.com/your-username/ani-downloader.git
cd ani-downloader
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Create Plugin Directory Structure
```
plugins/
├── your_plugin.py
└── __init__.py
```

## Understanding Plugin Architecture

### Core Components

1. **AnimePlugin Base Class**
   - All plugins inherit from this class
   - Defines the interface that plugins must implement

2. **PluginManager**
   - Loads and manages all plugins
   - Automatically detects which plugin to use for a URL

3. **Helper Library (`ani_plugin_helper.py`)**
   - Utilities for common plugin tasks
   - Simplifies web scraping and yt-dlp integration

### Plugin Interface

Every plugin must implement these methods:

```python
class MyPlugin(AnimePlugin):
    @property
    def name(self) -> str:
        """Plugin display name"""

    @property
    def domain(self) -> str:
        """Website domain (e.g., 'example.com')"""

    @property
    def supports_search(self) -> bool:
        """Whether plugin supports searching"""

    @property
    def supports_download(self) -> bool:
        """Whether plugin supports downloading"""

    def search_anime(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search for anime by query"""

    def get_anime_details(self, url: str) -> Tuple[Optional[str], str]:
        """Extract anime ID and title from URL"""

    def get_episode_list(self, anime_id: str) -> List[Dict[str, Any]]:
        """Get list of episodes for anime"""

    def get_video_servers(self, episode_token: str) -> List[Dict[str, Any]]:
        """Get available video servers for episode"""

    def get_video_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get video download data from server"""
```

## Creating Your First Plugin

### Step 1: Choose a Target Website

Let's create a plugin for a fictional anime site: `anime-example.com`

### Step 2: Analyze the Website

1. **Search Page**: `https://anime-example.com/search?keyword=naruto`
2. **Anime Page**: `https://anime-example.com/anime/naruto`
3. **Episode Page**: `https://anime-example.com/anime/naruto/episode-1`

### Step 3: Create the Plugin File

```python
from app.plugin_system import AnimePlugin
from ani_plugin_helper import AnimeSiteHelper
from typing import List, Dict, Optional, Tuple, Any
import re

class AnimeExamplePlugin(AnimePlugin):
    """Plugin for anime-example.com"""

    @property
    def name(self) -> str:
        return "Anime Example"

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
        self.helper = AnimeSiteHelper("https://anime-example.com")

    def search_anime(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search for anime"""
        search_url = f"https://anime-example.com/search?keyword={query}"
        soup = self.helper.get_soup(search_url)

        if not soup:
            return []

        # Find anime items
        anime_items = self.helper.find_anime_items(soup, [
            '.anime-list .item',
            '.search-results .anime-item'
        ])

        return anime_items[:max_results]

    def get_anime_details(self, url: str) -> Tuple[Optional[str], str]:
        """Get anime ID and title"""
        soup = self.helper.get_soup(url)
        if not soup:
            return None, "Unknown"

        # Extract anime ID from URL
        anime_id = url.split('/')[-1]

        # Extract title
        info = self.helper.extract_anime_info(soup)
        title = info.get('title', 'Unknown')

        return anime_id, title

    def get_episode_list(self, anime_id: str) -> List[Dict[str, Any]]:
        """Get episode list"""
        anime_url = f"https://anime-example.com/anime/{anime_id}"
        soup = self.helper.get_soup(anime_url)

        if not soup:
            return []

        episodes = []
        episode_links = soup.select('.episode-list a')

        for link in episode_links:
            episode_title = link.get_text(strip=True)
            episode_url = link.get('href')

            # Extract episode number
            ep_match = re.search(r'episode-(\d+)', episode_url or '')
            ep_num = int(ep_match.group(1)) if ep_match else len(episodes) + 1

            episodes.append({
                'episode_number': ep_num,
                'title': episode_title,
                'url': episode_url
            })

        return episodes

    def get_video_servers(self, episode_token: str) -> List[Dict[str, Any]]:
        """Get video servers"""
        soup = self.helper.get_soup(episode_token)
        if not soup:
            return []

        servers = []
        server_options = soup.select('.server-list option')

        for i, option in enumerate(server_options):
            servers.append({
                'id': f"server_{i}",
                'name': option.get_text(strip=True),
                'value': option.get('value')
            })

        return servers

    def get_video_data(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get video data"""
        # This would typically involve JavaScript execution or API calls
        # For this example, we'll use yt-dlp as fallback

        from ani_plugin_helper import YtDlpHelper

        # Extract video URL from page
        soup = self.helper.get_soup(server_id)
        if soup:
            video_url = soup.select_one('.video-player iframe')
            if video_url:
                iframe_src = video_url.get('src')
                if iframe_src:
                    return YtDlpHelper.extract_info(iframe_src)

        return None
```

### Step 4: Save and Test

Save your plugin as `plugins/anime_example.py` and restart the application.

## Using the Helper Library

The `ani_plugin_helper.py` library provides powerful utilities:

### AnimeSiteHelper

```python
from ani_plugin_helper import AnimeSiteHelper

helper = AnimeSiteHelper("https://example.com")

# Get page content
soup = helper.get_soup("https://example.com/anime/naruto")

# Extract common anime info
info = helper.extract_anime_info(soup)
print(f"Title: {info['title']}")
print(f"Description: {info['description']}")

# Find anime items
anime_list = helper.find_anime_items(soup, ['.anime-item'])
```

### YtDlpHelper

```python
from ani_plugin_helper import YtDlpHelper

# Extract video info
info = YtDlpHelper.extract_info("https://youtube.com/watch?v=...")
print(f"Title: {info['title']}")
print(f"Duration: {info['duration']}")

# Get best format
best_format = info['best_format']
print(f"Quality: {best_format['height']}p")

# Get direct download URL
video_url = YtDlpHelper.get_video_url("https://youtube.com/watch?v=...")
```

### PluginTemplate

```python
from ani_plugin_helper import PluginTemplate

# Generate basic plugin structure
template = PluginTemplate("My Anime Site", "myanime.com", "https://myanime.com")
plugin_code = template.create_basic_plugin()

# Save to file
with open('plugins/my_anime_plugin.py', 'w') as f:
    f.write(plugin_code)
```

## Advanced Plugin Features

### Handling JavaScript-Heavy Sites

Some sites use JavaScript to load content. Use Selenium or similar:

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class AdvancedPlugin(AnimePlugin):
    def __init__(self):
        options = Options()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)

    def get_dynamic_content(self, url: str):
        self.driver.get(url)
        # Wait for JavaScript to load
        time.sleep(3)
        return self.driver.page_source
```

### API-Based Sites

For sites with APIs:

```python
import requests

class ApiPlugin(AnimePlugin):
    def __init__(self):
        self.api_base = "https://api.anime-site.com"
        self.session = requests.Session()

    def search_anime(self, query: str, max_results: int = 20):
        response = self.session.get(f"{self.api_base}/search", params={'q': query})
        data = response.json()

        return [{
            'title': item['title'],
            'url': item['url'],
            'image': item['poster']
        } for item in data['results']]
```

### Custom Video Extraction

For sites not supported by yt-dlp:

```python
def get_video_data(self, server_id: str):
    soup = self.helper.get_soup(server_id)

    # Extract video URL from page
    video_element = soup.select_one('.video-player video source')
    if video_element:
        return {
            'url': video_element.get('src'),
            'format': 'mp4',
            'quality': '720p'
        }

    return None
```

## Testing Your Plugin

### Using PluginTester

```python
from ani_plugin_helper import PluginTester

# Test your plugin
tester = PluginTester(YourPlugin)
tester.run_basic_tests()
```

### Manual Testing

1. **Start the application**
```bash
python run.py
```

2. **Test search**
```python
import requests

# Login first
session = requests.Session()
session.post('http://localhost:5000/login', data={
    'username': 'admin',
    'password': 'admin'
})

# Test search
response = session.get('http://localhost:5000/api/search/anime', params={
    'query': 'naruto',
    'plugin': 'Your Plugin Name'
})
print(response.json())
```

3. **Test download**
```python
# Create download job
response = session.post('http://localhost:5000/api/download/create', json={
    'url': 'https://example.com/anime/naruto/episode-1',
    'plugin': 'Your Plugin Name'
})
print(response.json())
```

## Best Practices

### Code Quality
- Use descriptive variable names
- Add docstrings to all methods
- Handle errors gracefully
- Follow PEP 8 style guide

### Performance
- Implement rate limiting
- Cache results when possible
- Use efficient selectors
- Avoid unnecessary requests

### Error Handling
```python
def search_anime(self, query: str, max_results: int = 20):
    try:
        # Your search logic
        return results
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}")
        return []
```

### Security
- Validate all inputs
- Use HTTPS when possible
- Don't store sensitive data
- Sanitize HTML content

## Troubleshooting

### Common Issues

1. **Plugin not loading**
   - Check file name and location
   - Ensure class inherits from AnimePlugin
   - Check for syntax errors

2. **Search not working**
   - Verify website structure hasn't changed
   - Check selectors are correct
   - Test URL manually

3. **Download failing**
   - Check video URL extraction
   - Verify yt-dlp compatibility
   - Test with different episodes

### Debugging Tips

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints
def search_anime(self, query: str, max_results: int = 20):
    print(f"Searching for: {query}")
    soup = self.helper.get_soup(f"{self.base_url}/search?q={query}")
    print(f"Page loaded: {soup is not None}")

    # Continue debugging...
```

### Getting Help

- Check existing plugins for examples
- Read the helper library documentation
- Join the community Discord/forum
- Create an issue on GitHub

## Publishing Your Plugin

### Prepare Your Plugin

1. **Test thoroughly**
2. **Add documentation**
3. **Follow naming conventions**
4. **Include example usage**

### Share with Community

1. **Create a GitHub repository**
2. **Add to plugin registry** (if available)
3. **Share on forums/Discord**
4. **Write a blog post/tutorial**

### Plugin Registry

```json
{
    "name": "My Awesome Plugin",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "Plugin for awesome-anime.com",
    "supported_sites": ["awesome-anime.com"],
    "repository": "https://github.com/yourname/my-awesome-plugin"
}
```

## Updating the Application

### Method 1: Git Pull (Recommended)

If you cloned from GitHub:

```bash
# Backup your custom plugins and configurations
cp -r plugins/custom_plugins backup_plugins/
cp config.json backup_config.json

# Pull latest changes
git pull origin main

# Check for conflicts
git status

# If there are conflicts, resolve them
# Then restore your custom plugins
cp -r backup_plugins/* plugins/
```

### Method 2: Manual Download

1. **Download latest release** from GitHub
2. **Backup your data**:
   - `plugins/` directory (custom plugins)
   - `downloads/` directory (your anime)
   - `config.json` (if you have custom settings)
3. **Extract new version**
4. **Restore your backups**
5. **Update dependencies**: `pip install -r requirements.txt`

### Method 3: Docker Update

```bash
# Stop current container
docker-compose down

# Pull latest image
docker-compose pull

# Start updated container
docker-compose up -d
```

### Handling Updates

#### Configuration Changes
- Check `config.json` for new options
- Update your settings accordingly
- Backup before updating

#### Plugin Compatibility
- Test your custom plugins after update
- Update plugin code if needed
- Check for breaking changes in release notes

#### Database Migration
- If using database features, check migration scripts
- Backup database before update
- Run migration commands if provided

### Staying Updated

#### Watch Repository
- Star the GitHub repository
- Enable notifications for releases

#### Join Community
- Follow development on Discord/forum
- Participate in beta testing
- Contribute to development

#### Automatic Updates (Advanced)
```bash
# Create update script
#!/bin/bash
cd /path/to/ani-downloader
git pull origin main
pip install -r requirements.txt
systemctl restart ani-downloader
```

---

## Conclusion

You've now learned how to create plugins for Ani-Downloader! Remember:

1. **Start simple** - Create basic plugins first
2. **Use the helper library** - It makes development easier
3. **Test thoroughly** - Ensure your plugin works reliably
4. **Follow best practices** - Write clean, maintainable code
5. **Contribute back** - Share your plugins with the community

Happy plugin development! 🎉

## Additional Resources

- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Python Requests Documentation](https://docs.python-requests.org/)
- [Ani-Downloader GitHub](https://github.com/your-repo/ani-downloader)
- [Plugin Examples Repository](https://github.com/your-repo/plugin-examples)