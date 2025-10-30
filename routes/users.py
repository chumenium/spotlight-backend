"""
ユーザー管理API
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from utils.auth import jwt_required
from models.selectdata import get_user_name_iconpath,get_search_history,get_user_contents,get_spotlight_contents,get_play_history,get_user_spotlightnum
from models.updatedata import enable_notification, disable_notification,chenge_icon
from models.createdata import (
    add_content_and_link_to_users, insert_comment, insert_playlist, insert_playlist_detail,
    insert_search_history, insert_play_history, insert_notification
)
import os
import re
import base64

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


# ===============================
# 1️⃣ ユーザネームとアイコン画像のパスを取得
# ===============================
@users_bp.route('/getusername', methods=['POST'])
@jwt_required
def get_username():
    try:
        uid = request.user["firebase_uid"]
        username, iconimgpath = get_user_name_iconpath(uid)
        print(uid)
        print(username)
        print(iconimgpath)
        return jsonify({
            "status": "success",
            "data": {
                "username": username,
                "iconimgpath": iconimgpath
            }
        }), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 2️⃣ 検索履歴を取得
# ===============================
@users_bp.route('/getsearchhistory', methods=['POST'])
@jwt_required
def get_searchhistory():
    try:
        uid = request.user["firebase_uid"]
        searchhistory = get_search_history(uid)  # ["検索ワード1", "検索ワード2", ...]
        return jsonify({
            "status": "success",
            "data": searchhistory
        }), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 3️⃣ 通知設定をONにする
# ===============================
@users_bp.route('/notification/enable', methods=['POST'])
@jwt_required
def enable_user_notification():
    try:
        uid = request.user["firebase_uid"]
        enable_notification(uid)
        return jsonify({"status": "success", "message": "通知をONにしました"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 4️⃣ 通知設定をOFFにする
# ===============================
@users_bp.route('/notification/disable', methods=['POST'])
@jwt_required
def disable_user_notification():
    try:
        uid = request.user["firebase_uid"]
        disable_notification(uid)
        return jsonify({"status": "success", "message": "通知をOFFにしました"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400

# ===============================
# 2️⃣ 指定ユーザーが投稿したコンテンツ一覧を取得
# ===============================
@users_bp.route('/getusercontents', methods=['POST'])
@jwt_required
def get_user_contents_list():
    try:
        uid = request.user["firebase_uid"]
        rows = get_user_contents(uid)

        # Dartで扱いやすいようにdictに変換
        contents = [
            {
                "contentID": row[0],
                "title": row[1],
                "spotlightnum": row[2],
                "posttimestamp": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None,
                "playnum": row[4],
                "link": row[5],
                "thumbnailpath": row[6],
            }
            for row in rows
        ]

        return jsonify({"status": "success", "data": contents}), 200

    except Exception as e:
        print("⚠️エラー(get_user_contents_list):", e)
        return jsonify({"status": "error", "message": str(e)}), 400



# ===============================
# 3️⃣ スポットライト済みコンテンツ一覧を取得
# ===============================
@users_bp.route('/getspotlightcontents', methods=['POST'])
@jwt_required
def get_spotlight_contents_list():
    try:
        uid = request.user["firebase_uid"]
        rows = get_spotlight_contents(uid)

        contents = [
            {
                "contentID": row[0],
                "title": row[1],
                "spotlightnum": row[2],
                "posttimestamp": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None,
                "playnum": row[4],
                "link": row[5],
                "thumbnailpath": row[6],
            }
            for row in rows
        ]

        return jsonify({"status": "success", "data": contents}), 200

    except Exception as e:
        print("⚠️エラー(get_spotlight_contents_list):", e)
        return jsonify({"status": "error", "message": str(e)}), 400



# ===============================
# 4️⃣ 再生履歴コンテンツ一覧を取得
# ===============================
@users_bp.route('/getplayhistory', methods=['POST'])
@jwt_required
def get_play_history_list():
    try:
        uid = request.user["firebase_uid"]
        rows = get_play_history(uid)

        contents = [
            {
                "contentID": row[0],
                "title": row[1],
                "spotlightnum": row[2],
                "posttimestamp": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None,
                "playnum": row[4],
                "link": row[5],
                "thumbnailpath": row[6],
            }
            for row in rows
        ]

        return jsonify({"status": "success", "data": contents}), 200

    except Exception as e:
        print("⚠️エラー(get_play_history_list):", e)
        return jsonify({"status": "error", "message": str(e)}), 400


#プロフィールに遷移した場合の処理
@users_bp.route('/profile', methods=['POST'])
@jwt_required
def get_prolile_data():
    try:
        uid = request.user["firebase_uid"]
        spotlightnum = get_user_spotlightnum(uid)
        return jsonify({"status": "success", "spotlightnum": spotlightnum}), 200

    except Exception as e:
        print("⚠️エラー(get_play_history_list):", e)
        return jsonify({"status": "error", "message": str(e)}), 400


#アイコン変更の処理
@users_bp.route('/changeicon', methods=['POST'])
@jwt_required
def change_icon():
    try:
        uid = request.user["firebase_uid"]
        username = request.form.get("username")
        file = request.files.get("iconimg")

        if file:
            # ===== Base64文字列のヘッダーを除去 =====
            match = re.match(r"^data:image\/(png|jpeg|jpg|webp|gif);base64,(.+)$", file)
            if not match:
                return jsonify({
                    "status": "error",
                    "message": "不正な画像データです。"
                }), 400

            ext = match.group(1)
            img_data = base64.b64decode(match.group(2))

            # ===== 保存パス設定 =====
            save_dir = os.path.join(current_app.root_path, "icon")
            os.makedirs(save_dir, exist_ok=True)

            filename = f"{username}_icon.{ext}"
            save_path = os.path.join(save_dir, filename)

            # ===== 画像を保存 =====
            with open(save_path, "wb") as f:
                f.write(img_data)
        else:
            filename = "default_icon.jpg"
            iconimgpath = f"icon/{filename}"

        # ===== DBにパスを保存（相対パスで） =====
        iconimgpath = f"icon/{filename}"
        chenge_icon(uid, iconimgpath)

        return jsonify({
            "status": "success",
            "message": "アイコンを変更しました。",
            "iconimgpath": iconimgpath
        }), 200

    except Exception as e:
        print("⚠️エラー(change_icon):", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400