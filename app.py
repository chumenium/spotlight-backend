"""
SpotLight バックエンド API（リリース版）
Flask アプリケーション本番用エントリーポイント
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
import mimetypes
import re
from config import config

# Firebase Admin
import firebase_admin
from firebase_admin import credentials

# DB プール
from models.connection_pool import init_connection_pool

# ========================================
# Firebase 初期化（1回だけ）
# ========================================
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(BASE_DIR, "spotlight-597c4-firebase-adminsdk-fbsvc-e40a523651.json")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

except Exception as e:
    pass


# ========================================
# アプリ作成（systemd + gunicorn が使用）
# ========================================
def create_app(config_name='production'):
    app = Flask(__name__)

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 設定読込
    app.config.from_object(config[config_name])

    # DB 接続プール
    try:
        init_connection_pool()
    except Exception as e:
        pass

    # ========================================
    # Blueprint 読込
    # ========================================
    from routes.auth import auth_bp
    from routes.contents import content_bp
    from routes.users import users_bp
    from routes.delete import delete_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(delete_bp)
    app.register_blueprint(admin_bp)

    
    # ========================================
    # ヘルスチェック
    # ========================================
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "success": True,
            "data": {
                "status": "healthy",
                "message": "SpotLight API running"
            }
        }), 200

    # 404
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "error": {"code": 404, "message": "Not Found"}
        }), 404

    # 500
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({
            "success": False,
            "error": {"code": 500, "message": "Server Error"}
        }), 500

    return app


# ========================================
# 本番アプリインスタンス（Gunicorn 用）
# ========================================
app = create_app(os.getenv("FLASK_ENV", "production"))

# ========================================
# 開発環境のみローカルで起動
# （EC2本番では絶対に実行しない）
# ========================================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
