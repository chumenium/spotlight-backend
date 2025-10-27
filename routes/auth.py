"""
認証関連のエンドポイント
ユーザー登録、ログイン、Google認証など
"""
from flask import Blueprint, request, jsonify
from models.create_username import register_username
from models.userdate import update_FMCtoken, get_user_by_id, user_exists
from utils.auth import generate_jwt_token, verify_google_token
import jwt
import datetime
import psycopg2
from functools import wraps
from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, auth
from utils.auth import jwt_required

# ====== 設定 ======
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
# GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXP_HOURS = 24

if JWT_ALGORITHM != None and JWT_SECRET != None:
    print("✅ envfile read successfully")
else:
    print("⚠️ envfile read エラー")


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ====== Firebase認証 → DB登録 → JWT発行 ======
@auth_bp.route("/firebase", methods=["POST"])
def firebase_auth():
    data = request.get_json()
    id_token_str = data.get("id_token")
    token = data.get("token")  # 通知用トークン

    if not id_token_str:
        return jsonify({"error": "id_token is required"}), 400

    try:
        # Firebaseトークンを検証（Google/Apple/Twitter すべてOK）
        decoded_token = auth.verify_id_token(id_token_str)
        firebase_uid = decoded_token["uid"]

        #ユーザが存在するかを確認
        if not user_exists(firebase_uid):
            # DBに登録（ユーザ作成 or 更新）
            register_username(firebase_uid, token)

        # JWT発行
        jwt_token = jwt.encode({
            "firebase_uid": firebase_uid,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXP_HOURS)
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return jsonify({
            "status": "success",
            "jwt": jwt_token,
            "firebase_uid": firebase_uid
        })

    except Exception as e:
        print("🔥 Firebase認証エラー:", e)  # ← ここ追加！
        return jsonify({"error": str(e)}), 400



# ====== 通知トークン更新 ======
@auth_bp.route("/api/update_token", methods=["POST"])
@jwt_required
def update_token():
    data = request.get_json()
    new_token = data.get("token")
    if not new_token:
        return jsonify({"error": "token is required"}), 400
    try:
        uid = request.user["firebase_uid"]
        update_FMCtoken(new_token,uid)

        return jsonify({"status": "updated"})
    except Exception as e:
        print("エラー:", e)
        return jsonify({"error": str(e)}), 400

