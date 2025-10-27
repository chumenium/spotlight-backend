"""
検索機能API
コンテンツの検索と検索履歴管理機能を提供
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import jwt_required

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('/', methods=['GET'])
def search_content():
    """
    コンテンツを検索
    """