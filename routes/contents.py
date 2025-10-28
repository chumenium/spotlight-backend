"""
コンテンツ管理API
"""
from flask import Blueprint, request, jsonify
from utils.auth import jwt_required
from models.updatedata import (
    spotlight_on, spotlight_off,
    get_content_detail
)
from models.createdata import (
    insert_content, insert_comment, insert_playlist, insert_playlist_detail,
    insert_search_history, insert_play_history, insert_notification
)

import base64
import os
from datetime import datetime
from moviepy.editor import VideoFileClip
from PIL import Image
from io import BytesIO
from flask import current_app

content_bp = Blueprint('content', __name__, url_prefix='/api/content')


# ===============================
# 1️⃣ コンテンツ追加（動画・画像・音声に対応）
# ===============================
@content_bp.route('/add', methods=['POST'])
@jwt_required
def add_content():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()

        content_type = data.get("type")   # "video" | "image" | "audio"
        title = data.get("title")
        link = data.get("link")
        file_data = data.get("file")  # base64文字列を想定

        if not all([content_type, title, file_data]):
            return jsonify({"status": "error", "message": "必要なデータが不足しています"}), 400

        # ベースディレクトリ
        base_dir = os.path.join(current_app.root_path, "content")

        # サブディレクトリ設定
        paths = {
            "video": os.path.join(base_dir, "movie"),
            "image": os.path.join(base_dir, "picture"),
            "audio": os.path.join(base_dir, "audio"),
            "thumbnail": os.path.join(base_dir, "thumbnail")
        }
        for path in paths.values():
            os.makedirs(path, exist_ok=True)

        # ファイル名共通部分
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename_base = f"{uid}_{timestamp}"

        # === 種類別処理 ===
        if content_type == "video":
            if not VideoFileClip or not Image:
                return jsonify({"status": "error", "message": "moviepyまたはPillowがインストールされていません"}), 500

            video_path = os.path.join(paths["video"], f"{filename_base}.mp4")
            with open(video_path, "wb") as f:
                f.write(base64.b64decode(file_data))

            # サムネイル作成（1秒目のフレーム）
            clip = VideoFileClip(video_path)
            frame = clip.get_frame(1.0)
            thumb_path = os.path.join(paths["thumbnail"], f"{filename_base}_thumb.jpg")
            Image.fromarray(frame).save(thumb_path)
            clip.close()

            contentpath = f"content/movie/{filename_base}.mp4"
            thumbnailpath = f"content/thumbnail/{filename_base}_thumb.jpg"

        elif content_type == "image":
            if not Image:
                return jsonify({"status": "error", "message": "Pillowがインストールされていません"}), 500

            img_path = os.path.join(paths["picture"], f"{filename_base}.jpg")
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(file_data))
            # サムネイルとして同じ画像を使用
            thumb_path = os.path.join(paths["thumbnail"], f"{filename_base}_thumb.jpg")
            Image.open(img_path).save(thumb_path)

            contentpath = f"content/picture/{filename_base}.jpg"
            thumbnailpath = f"content/thumbnail/{filename_base}_thumb.jpg"

        elif content_type == "audio":
            audio_path = os.path.join(paths["audio"], f"{filename_base}.mp3")
            with open(audio_path, "wb") as f:
                f.write(base64.b64decode(file_data))
            thumbnailpath = "content/thumbnail/audio_default.png"
            contentpath = f"content/audio/{filename_base}.mp3"

        else:
            return jsonify({"status": "error", "message": "無効なtypeです（video/image/audio）"}), 400

        # --- DB登録 ---
        content_id = insert_content(
            contentpath=contentpath,
            thumbnailpath=thumbnailpath,
            link=link,
            title=title,
            userID=uid
        )

        return jsonify({
            "status": "success",
            "message": "コンテンツを追加しました。",
            "data": {
                "contentID": content_id,
                "contentpath": contentpath,
                "thumbnailpath": thumbnailpath
            }
        }), 200

    except Exception as e:
        print("⚠️エラー:", e)
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 400

# ===============================
# 2️⃣ コメント追加
# ===============================
@content_bp.route('/addcomment', methods=['POST'])
@jwt_required
def add_comment():
    try:
        uid = request.user["firebase_uid"]
        data = request.json
        insert_comment(
            contentID=data["contentID"],
            userID=uid,
            commenttext=data["commenttext"]
        )
        return jsonify({"status": "success", "message": "コメントを追加しました。"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 3️⃣ コンテンツ再生
# ===============================
@content_bp.route('/detail', methods=['POST'])
@jwt_required
def content_detail():
    try:
        contentID = request.json["contentID"]
        detail = get_content_detail(contentID)
        if not detail:
            return jsonify({"status": "error", "message": "コンテンツが見つかりません"}), 404

        return jsonify({
            "status": "success",
            "data": {
                "title": detail[0],
                "contentpath": detail[1],
                "spotlightnum": detail[2],
                "posttimestamp": detail[3].isoformat(),
                "playnum": detail[4],
                "link": detail[5],
                "username": detail[6],
                "iconimgpath": detail[7]
            }
        }), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 4️⃣ スポットライトON
# ===============================
@content_bp.route('/spotlight/on', methods=['POST'])
@jwt_required
def spotlight_on_route():
    try:
        uid = request.user["firebase_uid"]
        contentID = request.json["contentID"]
        spotlight_on(contentID, uid)
        return jsonify({"status": "success", "message": "スポットライトをONにしました"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 5️⃣ スポットライトOFF
# ===============================
@content_bp.route('/spotlight/off', methods=['POST'])
@jwt_required
def spotlight_off_route():
    try:
        uid = request.user["firebase_uid"]
        contentID = request.json["contentID"]
        spotlight_off(contentID, uid)
        return jsonify({"status": "success", "message": "スポットライトをOFFにしました"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400
