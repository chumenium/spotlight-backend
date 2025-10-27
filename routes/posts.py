"""
コンテンツ管理API
コンテンツの投稿、取得、更新、削除機能を提供
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import jwt_required
import os

posts_bp = Blueprint('posts', __name__, url_prefix='/api/posts')

@posts_bp.route('/', methods=['POST'])
def create_content():
    """
    新しいコンテンツを投稿
    """