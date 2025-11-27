"""
SpotLight バックエンド API
Flaskアプリケーションのメインファイル
"""

import os
import re
import mimetypes
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from config import config
from models.connection_pool import init_connection_pool


# =========================================================
# Firebase 初期化（アプリ起動時に一度だけ）
# =========================================================
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(BASE_DIR, "spotlight-597c4-firebase-adminsdk-fbsvc-e40a523651.json")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin initialized.")

except Exception as e:
    print(f"❌ Firebase初期化エラー: {e}")


# =========================================================
# Factory 関数（アプリ全体をここで作る）
# =========================================================
def create_app(config_name='default'):
    """
    Flaskアプリのファクトリー関数
    """
    app = Flask(__name__)

    # CORS（仮：本番は調整可）
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # -----------------------------------------------------
    # DBコネクションプール初期化
    # -----------------------------------------------------
    try:
        init_connection_pool()
        print("✅ Connection pool initialized.")
    except Exception as e:
        print(f"❌ DB初期化エラー: {e}")

    # -----------------------------------------------------
    # ディレクトリ設定
    # -----------------------------------------------------
    BASE_DIR = app.root_path
    ICON_DIR = os.path.join(BASE_DIR, 'icon')
    CONTENT_DIR = os.path.join(BASE_DIR, 'content')

    # =========================================================
    # Range対応のファイル送信（共通関数）
    # =========================================================
    def generate_file_chunks(file_path, chunk_size=128 * 1024):
        """ファイルをチャンク単位で読み込むジェネレーター"""
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    yield chunk
        except Exception as e:
            print(f"❌ ファイル読み込みエラー: {e}")
            raise

    def stream_with_range(file_path, mimetype):
        """Range対応のファイル送信"""
        try:
            size = os.path.getsize(file_path)
            range_header = request.headers.get("Range")

            if not range_header:
                res = Response(generate_file_chunks(file_path), mimetype=mimetype)
                res.headers['Content-Length'] = str(size)
                res.headers['Accept-Ranges'] = 'bytes'
                return res

            # 解析
            byte1, byte2 = 0, None
            m = re.search(r'bytes=(\d+)-(\d*)', range_header)
            if m:
                g = m.groups()
                byte1 = int(g[0])
                if g[1]:
                    byte2 = int(g[1])

            if byte1 >= size:
                return Response("Range Not Satisfiable", status=416)

            if byte2 is None or byte2 >= size:
                byte2 = size - 1

            length = byte2 - byte1 + 1

            with open(file_path, 'rb') as f:
                f.seek(byte1)
                data = f.read(length)

            res = Response(data, status=206, mimetype=mimetype)
            res.headers['Content-Range'] = f"bytes {byte1}-{byte2}/{size}"
            res.headers['Content-Length'] = str(length)
            res.headers['Accept-Ranges'] = "bytes"
            return res

        except Exception as e:
            print(f"❌ Range送信エラー: {e}")
            return jsonify({"error": "Failed to stream file"}), 500

    # =========================================================
    # 静的ファイル送信ルート
    # =========================================================
    @app.route('/icon/<path:filename>')
    def serve_icon(filename):
        file_path = os.path.join(ICON_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None:
            mimetype = 'image/jpeg'

        return stream_with_range(file_path, mimetype)

    @app.route('/content/movie/<path:filename>')
    def serve_movie(filename):
        file_path = os.path.join(CONTENT_DIR, 'movie', filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        return stream_with_range(file_path, 'video/mp4')

    @app.route('/content/audio/<path:filename>')
    def serve_audio(filename):
        file_path = os.path.join(CONTENT_DIR, 'audio', filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None:
            mimetype = 'audio/mpeg'

        return stream_with_range(file_path, mimetype)

    @app.route('/content/picture/<path:filename>')
    def serve_picture(filename):
        file_path = os.path.join(CONTENT_DIR, 'picture', filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None or not mimetype.startswith('image/'):
            mimetype = 'image/jpeg'

        return stream_with_range(file_path, mimetype)

    @app.route('/content/thumbnail/<path:filename>')
    def serve_thumbnail(filename):
        file_path = os.path.join(CONTENT_DIR, 'thumbnail', filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None:
            mimetype = 'image/jpeg'

        return stream_with_range(file_path, mimetype)

    # =========================================================
    # 設定読込
    # =========================================================
    app.config.from_object(config[config_name])

    # =========================================================
    # Blueprint 登録
    # =========================================================
    from routes.auth import auth_bp
    from routes.contents import content_bp
    from routes.users import users_bp
    from routes.delete import delete_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(delete_bp)

    # =========================================================
    # ヘルスチェック / ルートAPI
    # =========================================================
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"success": True, "data": {"status": "healthy"}})

    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            "success": True,
            "data": {
                "name": "SpotLight API",
                "version": "1.0.0",
                "description": "隠れた才能発見プラットフォーム",
                "endpoints": {
                    "auth": "/api/auth",
                    "posts": "/api/posts",
                    "comments": "/api/posts/<post_id>/comments",
                    "users": "/api/users",
                    "search": "/api/search",
                    "notifications": "/api/notifications",
                    "playhistory": "/api/playhistory",
                    "health": "/api/health"
                }
            }
        })

    # =========================================================
    # エラーハンドラー
    # =========================================================
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "error": {"code": 404, "message": "Not Found"}
        }), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({
            "success": False,
            "error": {"code": 500, "message": "Server Error"}
        }), 500

    return app


# =========================================================
# アプリ生成（systemd はこれを使う）
# =========================================================
app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
