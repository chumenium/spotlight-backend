"""
ユーザー管理API
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import jwt_required
from models.selectdata import get_user_name_iconpath,get_search_history

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

#ユーザネームとアイコン画像のパスを取得
@users_bp.route('/getusername', methods=['POST'])
@jwt_required
def get_username():
    try:
        uid = request.user["firebase_uid"]
        username,iconimgpath = get_user_name_iconpath(uid)
        return jsonify({
            "status": "success",
            "username": username,
            "iconimgpath": iconimgpath
        })
    except Exception as e:
        print("⚠️エラー:", e) 
        return jsonify({"error": str(e)}), 400

#検索履歴を取得
@users_bp.route('/getserchhistory', methods=['POST'])
@jwt_required
def get_serchhistory():
    try:
        uid = request.user["firebase_uid"]
        serchhistory = get_search_history(uid)#["検索ワード１","検索ワード２","検索ワード３"]
        return jsonify({
            "status": "success",
            "serchhistory": serchhistory,
        })
    except Exception as e:
        print("⚠️エラー:", e) 
        return jsonify({"error": str(e)}), 400