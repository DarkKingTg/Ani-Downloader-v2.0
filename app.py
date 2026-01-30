"""
Flask Web Application for AnimeKai Downloader
Main application entry point
"""
from flask import Flask
import os
from utils import create_download_folder

# Import blueprints
from routes.auth import auth_bp
from routes.pages import pages_bp
from routes.library import library_bp
from routes.download import download_bp
from routes.search import search_bp

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config['DOWNLOAD_FOLDER'] = 'downloads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB max
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Create downloads folder
    create_download_folder(app.config['DOWNLOAD_FOLDER'])
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(search_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    print("=" * 70)
    print("[ANIME] AnimeKai Downloader Web Interface")
    print("=" * 70)
    print("\n[SUCCESS] Server starting...")
    print("📡 Open your browser and navigate to: http://localhost:5000")
    print("\n🔐 Default Login: admin / admin")
    print("[WARNING] Make sure you have ffmpeg and yt-dlp installed!")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
