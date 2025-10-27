"""
プレイリスト管理API
プレイリストの作成、取得、コンテンツ追加・削除機能を提供
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import jwt_required

playlists_bp = Blueprint('playlists', __name__, url_prefix='/api/playlists')

@playlists_bp.route('/', methods=['POST'])
def create_playlist():
    """
    新しいプレイリストを作成
    """