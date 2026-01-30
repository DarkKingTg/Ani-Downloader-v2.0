"""
Search API Routes
Handles anime search on AnimeKai
"""
from flask import Blueprint, jsonify, request
from app.utils import login_required
from app.search import search_anime

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('/anime', methods=['GET'])
@login_required
def search_anime_api():
    """Search for anime by keyword with advanced filters"""
    query = request.args.get('q', '')
    genre = request.args.get('genre', '')
    year = request.args.get('year', '')
    status = request.args.get('status', '')
    sort_by = request.args.get('sort', 'relevance')
    page = int(request.args.get('page', 1))
    plugin_name = request.args.get('plugin', '')  # Optional: specify plugin
    
    if not query or len(query) < 2:
        return jsonify({"error": "Query must be at least 2 characters"}), 400
    
    try:
        from app.plugin_system import PluginManager
        plugin_manager = PluginManager()
        
        if plugin_name:
            # Search using specific plugin
            plugin = plugin_manager.plugins.get(plugin_name.lower())
            if not plugin or not plugin.supports_search:
                return jsonify({"error": f"Plugin '{plugin_name}' not found or doesn't support search"}), 400
            
            results = plugin.search_anime(query, max_results=20)
            # Add source info
            for result in results:
                result['source'] = plugin.domain
        else:
            # Use default AnimeKai search with advanced filtering
            from app.search import search_anime_advanced
            results = search_anime_advanced(
                query=query,
                genre=genre,
                year=year,
                status=status,
                sort_by=sort_by,
                page=page
            )
        
        return jsonify({
            "query": query,
            "filters": {
                "genre": genre,
                "year": year,
                "status": status,
                "sort": sort_by,
                "page": page,
                "plugin": plugin_name
            },
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@search_bp.route('/plugins', methods=['GET'])
@login_required
def get_available_plugins():
    """Get list of available plugins"""
    try:
        from app.plugin_system import PluginManager
        plugin_manager = PluginManager()
        plugins = plugin_manager.get_available_plugins()
        
        plugin_info = []
        for plugin in plugins:
            plugin_info.append({
                'name': plugin.name,
                'domain': plugin.domain,
                'supports_search': plugin.supports_search,
                'supports_download': plugin.supports_download
            })
        
        return jsonify({
            'plugins': plugin_info,
            'count': len(plugin_info)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
