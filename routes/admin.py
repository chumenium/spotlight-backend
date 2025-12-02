"""
管理者管理API
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from utils.auth import jwt_required
from models.admin_sql import (
    get_all_user_data, uid_admin_auth
)

from utils.s3 import upload_to_s3, get_cloudfront_url, delete_file_from_url


admin_bp = Blueprint('amdin', __name__, url_prefix='/api/admin')


# ===============================
# 全ユーザの情報取得
# ===============================
@admin_bp.route('/getusername', methods=['POST'])
@jwt_required
def get_username():
    try:
        userdatas = []
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            datas = get_all_user_data()
            
            for row in datas:
            # DBから取得したパスをCloudFront URLに正規化
                userdatas.append({
                    "userID": row[0],
                    "username": row[1],
                    "iconimgpath": row[2],
                    "admin": row[3],
                    "spotlightnum": row[4],
                    "reportnum": row[5],
                    "reportednum": row[6]
                })
            return jsonify({
                "status": "success",
                "userdatas" :userdatas
            }), 200
        else:
            print("⚠️エラー:", "⚠️⚠️管理者以外からのアクセスです⚠️⚠️")
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400

    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400