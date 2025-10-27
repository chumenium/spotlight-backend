"""
通知管理API
通知の取得、管理機能を提供
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import jwt_required

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/', methods=['GET'])
def get_notifications():
    """
    ユーザーの通知一覧を取得
    """
