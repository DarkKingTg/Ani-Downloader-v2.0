"""
Anikai Plugin
Handles search and download functionality for anikai.to
"""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.utils import Plugin
from app.routes.download import run_download_job
from flask import current_app

class AnikaiPlugin(Plugin):
    def search(self, query: str):
        # Placeholder for search functionality
        return f"Searching for {query} on anikai.to"

    def download(self, job, download_folder):
        try:
            run_download_job(job, download_folder)
        except Exception as e:
            current_app.logger.error(f"AnikaiPlugin download error: {e}")
            raise