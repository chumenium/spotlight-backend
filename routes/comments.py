"""
コメント管理API
コメントの投稿、取得、削除機能を提供
"""
from inspect import getcomments
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import jwt_required


comments_bp = Blueprint('comments', __name__, url_prefix='/api')


@comments_bp.route('/comments', methods=['GET'])
def get_comments():
    """
    コンテンツのコメント一覧を取得
    """
