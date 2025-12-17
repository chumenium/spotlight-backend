"""
認証関連のユーティリティ
"""
import jwt
from flask import request, jsonify
from functools import wraps
import os
import time
from threading import Lock

JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# リクエストデバウンス用のキャッシュ（コスト削減のため）
_request_cache = {}
_cache_lock = Lock()
_cache_ttl = 1.0  # 1秒以内の重複リクエストを無視

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


# ====== リクエストデバウンスデコレーター（コスト削減のため） ======
def debounce_request(ttl=_cache_ttl):
    """
    短時間の重複リクエストを防ぐデコレーター
    同じユーザーが短時間（デフォルト1秒）に同じエンドポイントを呼び出した場合、
    最初のリクエストだけを処理し、残りは429エラーを返す
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # JWT認証が必要な場合、ユーザーIDを取得
            uid = None
            if hasattr(request, 'user') and request.user:
                uid = request.user.get("firebase_uid")
            
            if uid:
                # キャッシュキーを生成（ユーザーID + エンドポイント + メソッド）
                cache_key = f"{uid}:{request.endpoint}:{request.method}"
                current_time = time.time()
                
                with _cache_lock:
                    # キャッシュに存在し、TTL内の場合
                    if cache_key in _request_cache:
                        last_time = _request_cache[cache_key]
                        elapsed = current_time - last_time
                        if elapsed < ttl:
                            # 重複リクエストとして429エラーを返す
                            # デバウンスされたリクエストはログ出力しない（正常な動作）
                            return jsonify({
                                "status": "error",
                                "message": "リクエストが頻繁すぎます。しばらく待ってから再度お試しください。"
                            }), 429
                    
                    # キャッシュを更新（リクエスト処理前に更新して、並行リクエストを防ぐ）
                    _request_cache[cache_key] = current_time
                    
                    # 古いキャッシュエントリを削除（メモリリーク防止）
                    if len(_request_cache) > 1000:
                        # 古いエントリを削除（TTLを超えたもの）
                        expired_keys = [
                            k for k, v in _request_cache.items()
                            if current_time - v > ttl * 2
                        ]
                        for k in expired_keys:
                            del _request_cache[k]
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
