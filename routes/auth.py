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



# ====== JWT認証デコレーター ======
def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        request.user = payload
        return f(*args, **kwargs)
    return decorated_function



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


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    ログイン処理
    Firebase IDトークンを使用してログインし、JWTを返す
    
    Request Body:
        {
            "id_token": "Firebase ID token",
            "token": "通知用トークン（オプショナル）"
        }
    
    Returns:
        JSON: ユーザー情報とJWTトークン
    """
    data = request.get_json()
    id_token_str = data.get("id_token")
    notification_token = data.get("token")
    
    if not id_token_str:
        return jsonify({"error": "id_token is required"}), 400
    
    try:
        # Firebaseトークンを検証
        decoded_token = auth.verify_id_token(id_token_str)
        firebase_uid = decoded_token["uid"]
        
        # DBにユーザーが存在するか確認
        if not user_exists(firebase_uid):
            # ユーザーが存在しない場合は新規登録
            if notification_token:
                register_username(firebase_uid, notification_token)
            else:
                register_username(firebase_uid, None)
        
        # ユーザー情報を取得
        user = get_user_by_id(firebase_uid)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # 通知トークンの更新（提供されている場合）
        if notification_token:
            update_FMCtoken(notification_token, firebase_uid)
        
        # JWT発行
        jwt_token = jwt.encode({
            "firebase_uid": firebase_uid,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXP_HOURS)
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return jsonify({
            "status": "success",
            "jwt": jwt_token,
            "firebase_uid": firebase_uid,
            "user": {
                "username": user["username"],
                "iconimgpath": user["iconimgpath"],
                "notificationenabled": user["notificationenabled"]
            }
        })
    
    except Exception as e:
        print("🔥 ログインエラー:", e)
        return jsonify({"error": str(e)}), 400

