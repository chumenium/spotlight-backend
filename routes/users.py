"""
ユーザー管理API
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from utils.auth import jwt_required
from models.selectdata import get_user_name_iconpath,get_search_history,get_user_contents,get_spotlight_contents,get_play_history,get_user_spotlightnum,get_notification,get_unloaded_num
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
        data = request.get_json()
        username = data.get("username")
        file = data.get("iconimg")
        if file:
            if file.startswith("data:image"):
                file = file.split(",")[1]
            
            # ===== 保存パス設定 =====
            save_dir = os.path.join(current_app.root_path, "icon")
            os.makedirs(save_dir, exist_ok=True)

            filename = f"{username}_icon.png"
            save_path = os.path.join(save_dir, filename)
            
            # ===== 画像を保存（ローカルサーバー） =====
            # Base64 → バイナリ書き込み
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(file))
        else:
            filename = "default_icon.jpg"
        
        iconimgpath = f"/icon/{filename}"

        # ===== DBにパスを保存（相対パスで） =====
        
        print(iconimgpath)
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


#通知一覧の取得処理
@users_bp.route('/notification', methods=['POST'])
@jwt_required
def get_notification_api():
    try:
        uid = request.user["firebase_uid"]
        rows = get_notification(uid)

        notification_list = []
        for row in rows:
            (
                notificationID,
                timestamp,
                contentuserCID,
                contentuserUID,
                spotlight_username,
                spotlight_title,
                comCTID,
                comCMID,
                comment_content_title,
                commenttext,
                parentcommentID,
                comment_username,
                notificationtext,
                notificationtitle,
                isread,
                spotlight_thumbnailpath,
                comment_thumbnailpath,
                spotlight_iconimgpath,
                comment_iconimgpath
            ) = row

            # 日付フォーマット
            timestamp_str = (
                timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else None
            )

            # 通知タイプ判定
            if contentuserCID:  # スポットライト通知
                contenttitle = spotlight_title
                title = "スポットライトが当てられました"
                text = f"{spotlight_username} さんがあなたの投稿にスポットライトを当てました"
                nt_type = "spotlight"
                iconpath = spotlight_iconimgpath
                thumbnailpath = spotlight_thumbnailpath
                contentID = contentuserCID
            #システム通知等のカスタム可能な通知
            elif notificationtext:
                nt_type = "system"
                contenttitle = None
                title = notificationtitle
                text = notificationtext
                thumbnailpath = None
                iconpath = "ここにシステム通知用のアイコンファイルパスを設定"
                contentID = None
            elif comCTID:  # コメント通知
                contenttitle = comment_content_title
                if parentcommentID:
                    text = f"{comment_username} さん：{commenttext}"
                    nt_type = "replycomment"
                    title = "コメントへの返信"
                else:
                    text = f"{comment_username} さん：{commenttext}"
                    nt_type = "newcomment"
                    title = "新しいコメント"
                iconpath = comment_iconimgpath
                thumbnailpath = comment_thumbnailpath
                contentID = comCTID

            notification_list.append({
                "notificationID": notificationID,
                "type": nt_type,
                "title": title,
                "text": text,
                "contenttitle":contenttitle,
                "iconpath":iconpath,
                "thumbnailpath":thumbnailpath,
                "contentID":contentID,
                "timestamp": timestamp_str,
                "isread":isread,
                
            })

        return jsonify({"status": "success", "data": notification_list}), 200

    except Exception as e:
        print("⚠️通知取得エラー:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

#未読通知数を取得する
@users_bp.route('/unloadednum', methods=['POST'])
@jwt_required
def get_unloaded_num_api():
    try:
        uid = request.user["firebase_uid"]
        num = get_unloaded_num(uid)
        return jsonify({"status": "success", "num": num}), 200
    except Exception as e:
        print("⚠️通知取得エラー:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400