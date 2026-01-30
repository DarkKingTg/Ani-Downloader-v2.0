"""
Search API Routes
Handles anime search on AnimeKai
"""
from flask import Blueprint, jsonify, request
from utils import login_required
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
    
    if not query or len(query) < 2:
        return jsonify({"error": "Query must be at least 2 characters"}), 400
    
    try:
        from app.search import search_anime_advanced
        results = search_anime_advanced(
            query=query,
            genre=genre,
            year=year,
            status=status,
            sort_by=sort_by,
            page=page
        )
        print(f"API: Got {len(results)} results")
        if results:
            print(f"API: First result keys: {list(results[0].keys())}")
        return jsonify({
            "query": query,
            "filters": {
                "genre": genre,
                "year": year,
                "status": status,
                "sort": sort_by,
                "page": page
            },
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500