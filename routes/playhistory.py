"""
再生履歴管理API
再生履歴の取得、管理機能を提供
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import jwt_required

playhistory_bp = Blueprint('playhistory', __name__, url_prefix='/api/playhistory')

@playhistory_bp.route('/', methods=['GET'])
def get_play_history():
    """
    ユーザーの再生履歴を取得
    """
