# Changelog

All notable changes to Ani-Downloader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-31

### 🎉 Major Release: Plugin System Overhaul

Ani-Downloader has been completely transformed with a powerful plugin system that extends support to 1000+ websites!

### ✨ Added

#### 🔌 Plugin System Architecture
- **Modular Plugin System**: Extensible architecture supporting any anime website
- **Automatic Plugin Detection**: Smart URL-based plugin selection
- **Plugin Manager**: Centralized plugin loading and management
- **Fallback Support**: Automatic fallback to yt-dlp for unsupported sites

#### 🛠️ Helper Library (`ani_plugin_helper.py`)
- **AnimeSiteHelper**: Common anime website patterns and utilities
- **YtDlpHelper**: yt-dlp integration with video quality selection
- **PluginTemplate**: Quick plugin scaffolding for developers
- **PluginTester**: Comprehensive testing utilities for plugin development
- **Rate Limiting**: Built-in request throttling to respect website limits
- **Error Handling**: Robust error handling and logging utilities

#### 📚 Documentation & Tutorials
- **Plugin Development Tutorial** (`PLUGIN_DEVELOPMENT_TUTORIAL.md`): Complete guide for creating plugins
- **Update Guide** (`UPDATE_GUIDE.md`): Comprehensive guide for updating from GitHub
- **Enhanced README**: Updated with plugin system documentation
- **Example Plugin**: Detailed example plugin with best practices

#### 🔍 Enhanced Search Features
- **Multi-Plugin Search**: Search across multiple anime sites simultaneously
- **Plugin Selection**: Manual plugin selection for targeted searches
- **Advanced Filters**: Enhanced search with quality and source filtering
- **Search API**: RESTful API endpoints for programmatic access

#### 📥 Download Enhancements
- **Universal Download Support**: Download from any yt-dlp supported website
- **Quality Selection**: Automatic best quality detection
- **Resume Support**: Improved download resume capabilities
- **Concurrent Downloads**: Enhanced multi-threaded downloading

#### 🎨 User Interface Improvements
- **Plugin Status Display**: Shows available plugins in the interface
- **Download Progress**: Real-time progress for all download sources
- **Error Notifications**: Better error reporting and user feedback
- **Responsive Design**: Improved mobile and desktop layouts

### 🔄 Changed

#### Core Architecture
- **Plugin-Aware Downloader**: Core download logic now supports plugins
- **Modular Search System**: Search functionality abstracted to plugins
- **API Endpoints**: Updated to support plugin parameters
- **Configuration**: Enhanced config options for plugin management

#### Dependencies
- **yt-dlp Integration**: Deeper integration for universal video support
- **BeautifulSoup4**: Enhanced HTML parsing capabilities
- **Requests**: Improved HTTP handling with rate limiting

### 🐛 Fixed
- **Download Reliability**: Improved error handling and retry logic
- **Search Accuracy**: Better search result filtering and validation
- **Memory Usage**: Optimized memory usage for large downloads
- **Cross-Platform**: Better Windows/Linux/Mac compatibility

### 📖 Developer Experience
- **Plugin Development Kit**: Complete toolkit for plugin creation
- **Testing Framework**: Automated testing for plugin validation
- **Code Examples**: Comprehensive examples and templates
- **Documentation**: Extensive guides and tutorials

### 🔒 Security
- **Input Validation**: Enhanced input sanitization
- **Rate Limiting**: Built-in protection against abuse
- **Error Logging**: Secure error reporting without sensitive data

### 📦 Built-in Plugins

#### Core Plugins
- **AnimeKai Plugin**: Enhanced original AnimeKai.to support
- **yt-dlp Generic Plugin**: Universal support for 1000+ websites
- **GogoAnime Plugin**: Example implementation for GogoAnime.is
- **Example Plugin**: Comprehensive template for new plugins

#### Supported Websites (via yt-dlp)
- YouTube, Vimeo, Dailymotion
- Crunchyroll, Funimation, Netflix (with cookies)
- Twitch, Bilibili, and hundreds more...

### 🚀 Migration Guide

#### For Users
1. **Backup your data** (downloads, config, custom plugins)
2. **Update using the guide** in `UPDATE_GUIDE.md`
3. **Test functionality** with your favorite anime sites
4. **Explore new features** like multi-site downloads

#### For Developers
1. **Review plugin interface** changes
2. **Update custom plugins** to new architecture
3. **Use helper library** for easier development
4. **Test with new testing framework**

### 🤝 Contributors
- **[@Cinichi](https://github.com/Cinichi)**: Original project creator
- **[@DarkKingTg](https://github.com/DarkKingTg)**: Plugin system implementation, helper library, documentation

### 📋 Full Feature List

#### Plugin System
- ✅ Automatic plugin detection
- ✅ Plugin manager with hot-reload
- ✅ Fallback to yt-dlp generic plugin
- ✅ Plugin development toolkit
- ✅ Comprehensive testing utilities

#### Enhanced Features
- ✅ Multi-website download support
- ✅ Advanced search with filters
- ✅ Quality selection and optimization
- ✅ Resume interrupted downloads
- ✅ Concurrent download management

#### Developer Tools
- ✅ Plugin template generator
- ✅ Helper library with utilities
- ✅ Complete documentation
- ✅ Example implementations
- ✅ Testing framework

---

## [1.0.0] - 2023-XX-XX

### ✨ Initial Release
- Basic AnimeKai.to support
- Simple web interface
- Single-threaded downloads
- Basic search functionality
- Docker support

---

## Version History

- **2.0.0** (2026-01-31): Plugin system overhaul - support for 1000+ websites
- **1.0.0** (2023): Initial release with AnimeKai.to support

## Upcoming Features

### Planned for v2.1.0
- [ ] Media server integration (Plex, Jellyfin)
- [ ] Advanced quality profiles
- [ ] Download scheduling
- [ ] Plugin marketplace
- [ ] Enhanced UI themes

### Long-term Vision
- [ ] Mobile app companion
- [ ] Browser extension
- [ ] API for third-party integrations
- [ ] Plugin development IDE
- [ ] Cloud sync capabilities

---

## How to Update

See [UPDATE_GUIDE.md](UPDATE_GUIDE.md) for detailed update instructions.

## Support

- 📖 [Documentation](README.md)
- 🛠️ [Plugin Tutorial](PLUGIN_DEVELOPMENT_TUTORIAL.md)
- 🆘 [Issues](https://github.com/DarkKingTg/Ani-Downloader/issues)
- 💬 [Discussions](https://github.com/DarkKingTg/Ani-Downloader/discussions)

---

*Made with ❤️ by the Ani-Downloader community*