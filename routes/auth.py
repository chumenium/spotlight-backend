"""
認証関連のエンドポイント
ユーザー登録、ログイン、Google認証など
"""
from flask import Blueprint, request, jsonify
from models.create_username import register_username
from models.selectdata import user_exists
from models.updatedata import update_FMCtoken
#from utils.auth import generate_jwt_token, verify_google_token
import jwt
import datetime
from functools import wraps
from dotenv import load_dotenv
import os
from firebase_admin import credentials, auth
from utils.auth import jwt_required
from utils.s3 import get_cloudfront_url
from models.updatedata import chenge_icon


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
def handle_firebase_auth():
    """Firebase認証の共通処理（Google/Apple/Twitter すべてOK）"""
    data = request.get_json() or {}
    id_token_str = data.get("id_token")or data.get("idToken")

    if not id_token_str:
        return jsonify({"error": "id_token is required"}), 400

    try:
        # Firebaseトークンを検証（Google/Apple/Twitter すべてOK）
        decoded_token = auth.verify_id_token(id_token_str)
        firebase_uid = decoded_token["uid"]

        #ユーザが存在するかを確認
        if not user_exists(firebase_uid):
            # DBに登録（ユーザ作成 or 更新）
            token = data.get("token")  # 通知用トークン
            register_username(firebase_uid, token)
            filename = "default_icon.jpg"
            #デフォルトアイコンを設定
            iconimgpath = get_cloudfront_url("icon", filename)
            chenge_icon(firebase_uid, iconimgpath)

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
        print("🔥 Firebase認証エラー:", e)
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/firebase", methods=["POST"])
def firebase_auth():
    """Firebase認証エンドポイント"""
    return handle_firebase_auth()


@auth_bp.route("/google", methods=["POST"])
def google_auth():
    """Google認証エンドポイント（Firebase認証を使用）"""
    return handle_firebase_auth()



# ====== 通知トークン更新 ======
@auth_bp.route("/update_token", methods=["POST"])
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

