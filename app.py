"""
SpotLight バックエンド API
Flaskアプリケーションのメインファイル
"""
from flask import Flask, jsonify, send_from_directory, send_file, Response, request
from flask_cors import CORS
import os
import mimetypes
import re

# 設定のインポート
from config import config

# ルート（エンドポイント）のインポート

import firebase_admin
from firebase_admin import credentials
from models.connection_pool import init_connection_pool

# ====== Firebase初期化（アプリ起動時に一度だけ） ======
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(BASE_DIR, "spotlight-597c4-firebase-adminsdk-fbsvc-8820bfe6ef.json")

    if not firebase_admin._apps:  # ← 二重初期化防止
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized successfully.")

except Exception as e:
    print(f"⚠️ Firebase初期化エラー: {e}")



def create_app(config_name='default'):
    """
    Flaskアプリケーションのファクトリー関数
    
    Args:
        config_name (str): 設定名（development, production, default）
    
    Returns:
        Flask: Flaskアプリケーションインスタンス
    """
    # Flaskアプリケーションの初期化
    app = Flask(__name__)
    init_connection_pool()
    

    
    # === 各ディレクトリの定義 ===
    BASE_DIR = app.root_path
    ICON_DIR = os.path.join(BASE_DIR, 'icon')
    CONTENT_DIR = os.path.join(BASE_DIR, 'content')


    # ============================================
    # 汎用：チャンク（分割）送信関数
    # ============================================
    def generate_file_chunks(file_path, chunk_size=128 * 1024):  # 128KB
        """ファイルをチャンク単位で読み込むジェネレーター"""
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    yield chunk
        except Exception as e:
            print(f"⚠️ ファイル読み込みエラー: {e}")
            raise


    # ============================================
    # Rangeリクエスト対応（動画・音声・画像など）
    # ============================================
    def stream_with_range_support(file_path, mimetype):
        """HTTP Range対応の部分送信"""
        try:
            size = os.path.getsize(file_path)
            range_header = request.headers.get('Range', None)

            # Range指定なし → 通常ストリーミング
            if not range_header:
                response = Response(generate_file_chunks(file_path), mimetype=mimetype)
                response.headers['Content-Length'] = str(size)
                response.headers['Accept-Ranges'] = 'bytes'
                response.headers['Cache-Control'] = 'public, max-age=3600'
                return response

            # Rangeヘッダの解析
            byte1, byte2 = 0, None
            match = re.search(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                g = match.groups()
                byte1 = int(g[0])
                if g[1]:
                    byte2 = int(g[1])

            if byte1 >= size:
                return Response('Range Not Satisfiable', status=416)

            if byte2 is None or byte2 >= size:
                byte2 = size - 1

            length = byte2 - byte1 + 1

            # 指定範囲を読み込む
            with open(file_path, 'rb') as f:
                f.seek(byte1)
                data = f.read(length)

            response = Response(data, status=206, mimetype=mimetype)
            response.headers['Content-Range'] = f'bytes {byte1}-{byte2}/{size}'
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Length'] = str(length)
            response.headers['Cache-Control'] = 'public, max-age=3600'
            return response

        except Exception as e:
            print(f"⚠️ Range送信エラー: {e}")
            return jsonify({"error": "Failed to stream file"}), 500


    # ============================================
    # 1️⃣ アイコン送信（チャンク送信）
    # ============================================
    @app.route('/icon/<path:filename>')
    def serve_icon(filename):
        try:
            file_path = os.path.join(ICON_DIR, filename)
            if not os.path.exists(file_path):
                return jsonify({"error": "File not found"}), 404

            mimetype, _ = mimetypes.guess_type(file_path)
            if mimetype is None or not mimetype.startswith('image/'):
                mimetype = 'image/jpeg'

            return stream_with_range_support(file_path, mimetype)

        except Exception as e:
            print(f"⚠️ アイコン送信エラー: {e}")
            return jsonify({"error": "Failed to serve icon"}), 500


    # ============================================
    # 2️⃣ 動画送信（Range対応・分割送信）
    # ============================================
    @app.route('/content/movie/<path:filename>')
    def serve_movie(filename):
        try:
            file_path = os.path.join(CONTENT_DIR, 'movie', filename)
            if not os.path.exists(file_path):
                return jsonify({"error": "File not found"}), 404

            return stream_with_range_support(file_path, mimetype='video/mp4')
        except Exception as e:
            print(f"⚠️ 動画送信エラー: {e}")
            return jsonify({"error": "Failed to serve movie"}), 500


    # ============================================
    # 3️⃣ 音声送信（Range対応・分割送信）
    # ============================================
    @app.route('/content/audio/<path:filename>')
    def serve_audio(filename):
        try:
            file_path = os.path.join(CONTENT_DIR, 'audio', filename)
            if not os.path.exists(file_path):
                return jsonify({"error": "File not found"}), 404

            mimetype, _ = mimetypes.guess_type(file_path)
            if mimetype is None:
                mimetype = 'audio/mpeg'

            return stream_with_range_support(file_path, mimetype)
        except Exception as e:
            print(f"⚠️ 音声送信エラー: {e}")
            return jsonify({"error": "Failed to serve audio"}), 500


    # ============================================
    # 4️⃣ 画像送信（Range対応）
    # ============================================
    @app.route('/content/picture/<path:filename>')
    def serve_picture(filename):
        try:
            file_path = os.path.join(CONTENT_DIR, 'picture', filename)
            if not os.path.exists(file_path):
                return jsonify({"error": "File not found"}), 404

            mimetype, _ = mimetypes.guess_type(file_path)
            if mimetype is None or not mimetype.startswith('image/'):
                mimetype = 'image/jpeg'

            return stream_with_range_support(file_path, mimetype)

        except Exception as e:
            print(f"⚠️ 画像送信エラー: {e}")
            return jsonify({"error": "Failed to serve picture"}), 500


    # ============================================
    # 5️⃣ サムネイル送信（Range対応）
    # ============================================
    @app.route('/content/thumbnail/<path:filename>')
    def serve_thumbnail(filename):
        try:
            file_path = os.path.join(CONTENT_DIR, 'thumbnail', filename)
            if not os.path.exists(file_path):
                return jsonify({"error": "File not found"}), 404

            mimetype, _ = mimetypes.guess_type(file_path)
            if mimetype is None or not mimetype.startswith('image/'):
                mimetype = 'image/jpeg'

            return stream_with_range_support(file_path, mimetype)

        except Exception as e:
            print(f"⚠️ サムネイル送信エラー: {e}")
            return jsonify({"error": "Failed to serve thumbnail"}), 500






    # # === 静的ファイルのルート定義 ===
    # @app.route('/icon/<path:filename>')
    # def serve_icon(filename):
    #     icon_dir = os.path.join(app.root_path, 'icon')
    #     file_path = os.path.join(icon_dir, filename)
        
    #     if not os.path.exists(file_path):
    #         return jsonify({"error": "File not found"}), 404
        
    #     # ファイルサイズを取得
    #     file_size = os.path.getsize(file_path)
        
    #     # 大きなファイル（100KB以上）の場合はsend_fileを使用
    #     # 小さなファイルはsend_from_directoryを使用（既に動作確認済み）
    #     if file_size > 100 * 1024:  # 100KB以上
    #         mimetype, _ = mimetypes.guess_type(file_path)
    #         if mimetype is None:
    #             mimetype = 'image/jpeg'
    #         # send_fileを使用し、conditional=Falseで条件付きリクエストを無効化
    #         print("読み込もうとしたファイルは100KB以上です")
    #         return send_file(
    #             file_path,
    #             mimetype=mimetype,
    #             conditional=False,  # ETagや条件付きリクエストを無効化
    #             as_attachment=False
    #         )
    #     else:
    #         # 小さなファイルは従来通りsend_from_directoryを使用
    #         return send_from_directory(icon_dir, filename)

    # @app.route('/content/movie/<path:filename>')
    # def serve_movie(filename):
    #     movie_dir = os.path.join(app.root_path, 'content', 'movie')
    #     return send_from_directory(movie_dir, filename)

    # @app.route('/content/audio/<path:filename>')
    # def serve_audio(filename):
    #     audio_dir = os.path.join(app.root_path, 'content', 'audio')
    #     return send_from_directory(audio_dir, filename)

    # @app.route('/content/picture/<path:filename>')
    # def serve_picture(filename):
    #     picture_dir = os.path.join(app.root_path, 'content', 'picture')
    #     return send_from_directory(picture_dir, filename)

    # @app.route('/content/thumbnail/<path:filename>')
    # def serve_thumbnail(filename):
    #     thumbnail_dir = os.path.join(app.root_path, 'content', 'thumbnail')
    #     return send_from_directory(thumbnail_dir, filename)
    


    # 設定の読み込み
    app.config.from_object(config[config_name])
    
    # CORSの設定
    # 開発環境ではすべてのオリジンを許可（本番環境では制限すること）
    cors_origins = app.config['CORS_ORIGINS']
    
    # 開発環境（DEBUG=True）の場合はすべてのオリジンを許可
    if app.config.get('DEBUG', False):
        cors_resources = {
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": False
            },
            r"/icon/*": {
                "origins": "*",
                "methods": ["GET", "OPTIONS"],
                "allow_headers": ["Content-Type"],
                "supports_credentials": False
            },
            r"/content/*": {
                "origins": "*",
                "methods": ["GET", "OPTIONS"],
                "allow_headers": ["Content-Type"],
                "supports_credentials": False
            }
        }
    elif cors_origins == ['*']:
        # すべてのオリジンを許可する場合（明示的に指定された場合）
        cors_resources = {
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": False
            },
            r"/icon/*": {
                "origins": "*",
                "methods": ["GET", "OPTIONS"],
                "allow_headers": ["Content-Type"],
                "supports_credentials": False
            },
            r"/content/*": {
                "origins": "*",
                "methods": ["GET", "OPTIONS"],
                "allow_headers": ["Content-Type"],
                "supports_credentials": False
            }
        }
    else:
        # 特定のオリジンのみ許可
        cors_resources = {
            r"/api/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            },
            r"/icon/*": {
                "origins": cors_origins,
                "methods": ["GET", "OPTIONS"],
                "allow_headers": ["Content-Type"]
            },
            r"/content/*": {
                "origins": cors_origins,
                "methods": ["GET", "OPTIONS"],
                "allow_headers": ["Content-Type"]
            }
        }
    
    CORS(app, resources=cors_resources)
    
    from routes.auth import auth_bp
    from routes.contents import content_bp
    from routes.users import users_bp
    # Blueprintの登録
    app.register_blueprint(auth_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(users_bp)
    
    from flask import Blueprint, request, jsonify
    from models.selectdata import get_user_name_iconpath


    # @app.route('/test', methods=['GET'])
    # def test():
    #     try:
    #         # data = request.get_json()
    #         # userid = data.get("userid")
    #         userid = request.args.get('userid')
    #         username = get_user_name_iconpath(userid)

    #         return jsonify({
    #             "status": "success",
    #             "username": username
    #         })
    #     except Exception as e:
    #         print("エラー:", e)
    #         return jsonify({"error": str(e)}), 400


    # ヘルスチェックエンドポイント
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """
        ヘルスチェック
        サーバーの稼働状況を確認
        """
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'message': 'SpotLight API is running'
            }
        }), 200
    
    # ルートエンドポイント
    @app.route('/', methods=['GET'])
    def root():
        """
        ルートエンドポイント
        APIの基本情報を返す
        """
        return jsonify({
            'success': True,
            'data': {
                'name': 'SpotLight API',
                'version': '1.0.0',
                'description': '隠れた才能発見プラットフォーム',
                'endpoints': {
                    'auth': '/api/auth',
                    'posts': '/api/posts',
                    'comments': '/api/posts/<post_id>/comments',
                    'search': '/api/search',
                    'users': '/api/users',
                    'notifications': '/api/notifications',
                    'playlists': '/api/playlists',
                    'playhistory': '/api/playhistory',
                    'health': '/api/health'
                }
            }
        }), 200
    
    # エラーハンドラー
    @app.errorhandler(404)
    def not_found(error):
        """404エラーハンドラー"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'RESOURCE_NOT_FOUND',
                'message': 'The requested resource was not found'
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500エラーハンドラー"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': 'Internal server error occurred'
            }
        }), 500
    
    @app.errorhandler(401)
    def unauthorized(error):
        """401エラーハンドラー"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'AUTHENTICATION_ERROR',
                'message': 'Authentication required'
            }
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """403エラーハンドラー"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'AUTHORIZATION_ERROR',
                'message': 'You do not have permission to access this resource'
            }
        }), 403
    
    return app

# アプリケーションインスタンスの作成
app = create_app(os.getenv('FLASK_ENV', 'development'))


if __name__ == '__main__':
    # 開発サーバーの起動
    print("=" * 60)
    print("SpotLight API Server Starting...")
    print("=" * 60)
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Host: {app.config['HOST']}")
    print(f"Port: {app.config['PORT']}")
    print(f"Debug: {app.config['DEBUG']}")
    print("=" * 60)
    # print("\nAvailable endpoints:")
    # print("  - GET  /")
    # print("  - GET  /api/health")
    # print("  - POST /api/auth/register")
    # print("  - POST /api/auth/login")
    # print("  - POST /api/auth/google")
    # print("  - GET  /api/posts")
    # print("  - POST /api/posts")
    # print("  - GET  /api/posts/<post_id>")
    # print("  - POST /api/posts/<post_id>/spotlight")
    # print("  - GET  /api/posts/<post_id>/comments")
    # print("  - POST /api/posts/<post_id>/comments")
    # print("  - GET  /api/search")
    # print("  - GET  /api/users/<user_id>")
    # print("  - PUT  /api/users/<user_id>")
    # print("  - GET  /api/users/<user_id>/profile")
    # print("  - GET  /api/users/<user_id>/stats")
    # print("  - GET  /api/notifications")
    # print("  - GET  /api/notifications/count")
    # print("  - DELETE /api/notifications/<notification_id>")
    # print("  - DELETE /api/notifications/clear")
    # print("  - POST /api/playlists")
    # print("  - GET  /api/playlists/user/<user_id>")
    # print("  - GET  /api/playlists/<playlist_id>/contents")
    # print("  - POST /api/playlists/<playlist_id>/contents")
    # print("  - DELETE /api/playlists/<playlist_id>/contents/<content_id>")
    # print("  - DELETE /api/playlists/<playlist_id>")
    # print("  - GET  /api/playhistory")
    # print("  - POST /api/playhistory")
    # print("  - DELETE /api/playhistory/clear")
    # print("  - GET  /api/playhistory/stats")
    print("=" * 60)
    print("\nPress CTRL+C to quit\n")
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
