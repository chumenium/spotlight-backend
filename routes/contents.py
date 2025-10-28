"""
コンテンツ管理API
コンテンツの投稿、取得、削除機能を提供
"""
from inspect import getcomments
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import jwt_required
from models.selectdata import get_content_detail
import random


contents_bp = Blueprint('contents', __name__, url_prefix='/api')


@contents_bp.route('/contents', methods=['POST'])
def get_contents():
    try:
        data = request.get_json()
        contentid = data.get("contentid")
        pcn = data.get("pcn")#すでに読み込んだコンテンツのコンテンツIDをリスト化したもの[1,5,7,3,10]
        contentdetail = get_content_detail(contentid)
        nextcontentid = 0
        return jsonify({
            "status": "success",
            "contentdetail": contentdetail,
            "nextcontentid":nextcontentid
        })

    except Exception as e:
        print("エラー:", e)  # ← ここ追加！
        return jsonify({"error": str(e)}), 400