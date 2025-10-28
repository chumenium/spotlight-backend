"""
ユーザー管理API
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import jwt_required
from models.selectdata import get_user_name_iconpath,get_search_history
from models.updatedata import enable_notification, disable_notification

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


# ===============================
# 1️⃣ ユーザネームとアイコン画像のパスを取得
# ===============================
@users_bp.route('/getusername', methods=['POST'])
@jwt_required
def get_username():
    try:
        uid = request.user["firebase_uid"]
        username, iconimgpath = get_user_name_iconpath(uid)
        return jsonify({
            "status": "success",
            "data": {
                "username": username,
                "iconimgpath": iconimgpath
            }
        }), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 2️⃣ 検索履歴を取得
# ===============================
@users_bp.route('/getsearchhistory', methods=['POST'])
@jwt_required
def get_searchhistory():
    try:
        uid = request.user["firebase_uid"]
        searchhistory = get_search_history(uid)  # ["検索ワード1", "検索ワード2", ...]
        return jsonify({
            "status": "success",
            "data": searchhistory
        }), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 3️⃣ 通知設定をONにする
# ===============================
@users_bp.route('/notification/enable', methods=['POST'])
@jwt_required
def enable_user_notification():
    try:
        uid = request.user["firebase_uid"]
        enable_notification(uid)
        return jsonify({"status": "success", "message": "通知をONにしました"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 4️⃣ 通知設定をOFFにする
# ===============================
@users_bp.route('/notification/disable', methods=['POST'])
@jwt_required
def disable_user_notification():
    try:
        uid = request.user["firebase_uid"]
        disable_notification(uid)
        return jsonify({"status": "success", "message": "通知をOFFにしました"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400