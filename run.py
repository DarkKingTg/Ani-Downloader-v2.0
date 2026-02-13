"""
AnimeKai Downloader - Application Entry Point
Run this file to start the web server
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, socketio

if __name__ == '__main__':
    app = create_app()
    
    print("=" * 70)
    print("🎬 AnimeKai Downloader Web Interface")
    print("=" * 70)
    print("\n✅ Server starting...")
    print("📡 Open your browser: http://localhost:5000")
    print("\n🔐 Default Login: admin / admin")
    print("⚠️  Requires: ffmpeg and yt-dlp")
    print("\n💡 Customize with environment variables:")
    print("   ANIME_USER, ANIME_PASS, SECRET_KEY, DOWNLOAD_FOLDER")
    print("=" * 70)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
