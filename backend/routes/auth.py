"""
認証関連のエンドポイント
ユーザー登録、ログイン、Google認証など
"""
from flask import Blueprint, request, jsonify
from models.create_username import create_username
from utils.auth import generate_jwt_token, verify_google_token
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
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
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS"))
# ====== JWT認証デコレーター ======
# def jwt_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         auth_header = request.headers.get("Authorization", "")
#         if not auth_header.startswith("Bearer "):
#             return jsonify({"error": "Missing or invalid Authorization header"}), 401
#         token = auth_header.split(" ")[1]
#         try:
#             payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
#         except jwt.ExpiredSignatureError:
#             return jsonify({"error": "Token has expired"}), 401
#         except jwt.InvalidTokenError:
#             return jsonify({"error": "Invalid token"}), 401
#         request.user = payload
#         return f(*args, **kwargs)
#     return decorated_function

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# Firebase初期化（アプリ起動時に一度だけ）
cred = credentials.Certificate("spotlight-597c4-firebase-adminsdk-fbsvc-8820bfe6ef.json")
firebase_admin.initialize_app(cred)
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
        create_username(firebase_uid, token)

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
        return jsonify({"error": str(e)}), 400

# ====== 通知トークン更新 ======
@auth_bp.route("/api/update_token", methods=["POST"])
@jwt_required
def update_token():
    data = request.get_json()
    new_token = data.get("token")
    if not new_token:
        return jsonify({"error": "token is required"}), 400

    uid = request.user["firebase_uid"]

    # conn = get_db_connection()
    # cur = conn.cursor()
    # cur.execute("UPDATE \"user\" SET token = %s WHERE userID = %s", (new_token, uid))
    # conn.commit()
    # cur.close()
    # conn.close()

    return jsonify({"status": "updated"})



@auth_bp.route('/register', methods=['POST'])
def register():
    """
    ユーザー登録
    
    Request Body:
        {
            "nickname": "ユーザー名",
            "email": "user@example.com",
            "password": "password123"
        }
    
    Returns:
        JSON: ユーザー情報とJWTトークン
    """
    try:
        data = request.get_json()
        nickname = data.get('nickname')
        email = data.get('email')
        password = data.get('password')
        
        # バリデーション
        if not all([nickname, email, password]):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'All fields are required'
                }
            }), 400
        
        # TODO: DB担当メンバーがユーザー登録処理を実装
        # - パスワードのハッシュ化
        # - ユーザーの重複チェック
        # - データベースへの保存
        
        # モックレスポンス
        user_data = {
            'id': 'user_mock_123',
            'nickname': nickname,
            'email': email,
            'profileImageUrl': None,
            'createdAt': '2024-01-01T00:00:00Z'
        }
        
        # JWTトークン生成
        token = generate_jwt_token({
            'user_id': user_data['id'],
            'email': email,
            'nickname': nickname
        })
        
        return jsonify({
            'success': True,
            'data': {
                'user': user_data,
                'token': token
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    ログイン
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "password123"
        }
    
    Returns:
        JSON: ユーザー情報とJWTトークン
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # バリデーション
        if not all([email, password]):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Email and password are required'
                }
            }), 400
        
        # TODO: DB担当メンバーがログイン処理を実装
        # - ユーザーの存在確認
        # - パスワードの検証
        # - ユーザー情報の取得
        
        # モックレスポンス
        user_data = {
            'id': 'user_mock_123',
            'nickname': 'テストユーザー',
            'email': email,
            'profileImageUrl': 'https://example.com/avatar.jpg',
            'followersCount': 100,
            'followingCount': 50,
            'postsCount': 25
        }
        
        # JWTトークン生成
        token = generate_jwt_token({
            'user_id': user_data['id'],
            'email': email,
            'nickname': user_data['nickname']
        })
        
        return jsonify({
            'success': True,
            'data': {
                'user': user_data,
                'token': token
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500

@auth_bp.route('/google', methods=['POST'])
def google_auth():
    """
    Google認証
    
    Request Body:
        {
            "id_token": "google_id_token_here"
        }
    
    Returns:
        JSON: ユーザー情報とJWTトークン
    """
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        
        if not id_token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'id_token is required'
                }
            }), 400
        
        # Googleトークンの検証
        google_user = verify_google_token(id_token)
        
        # TODO: DB担当メンバーがGoogle認証処理を実装
        # - Googleアカウント情報でユーザー検索
        # - 存在しない場合は新規作成
        # - ユーザー情報の取得
        
        # JWTトークン生成
        token = generate_jwt_token({
            'google_id': google_user['google_id'],
            'email': google_user['email'],
            'name': google_user['name']
        })
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'email': google_user['email'],
                    'name': google_user['name'],
                    'picture': google_user['picture']
                },
                'token': token
            }
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'AUTHENTICATION_ERROR',
                'message': 'Invalid Google token'
            }
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500

