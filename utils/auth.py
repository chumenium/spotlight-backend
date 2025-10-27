"""
認証関連のユーティリティ
"""
import jwt
from flask import request, jsonify
from functools import wraps
import os

JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

"""
dart側で通信する際に毎回以下をbodyに追加
'Authorization': 'Bearer $jwt',
"""
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

        # Flaskのrequestオブジェクトにユーザー情報を一時的に追加
        request.user = payload
        return f(*args, **kwargs)
    return decorated_function
