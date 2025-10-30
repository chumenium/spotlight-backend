"""
コンテンツ管理API
"""
from flask import Blueprint, request, jsonify
from utils.auth import jwt_required
from models.updatedata import spotlight_on, spotlight_off
from models.selectdata import get_content_detail,get_user_spotlight_flag,get_comments_by_content,get_play_content_id,get_search_contents, get_playlists_with_thumbnail, get_playlist_contents
from models.createdata import (
    add_content_and_link_to_users, insert_comment, insert_playlist, insert_playlist_detail,
    insert_search_history, insert_play_history, insert_notification
)

import base64
import os
from datetime import datetime
from flask import current_app


content_bp = Blueprint('content', __name__, url_prefix='/api/content')


# ===============================
# 1️⃣ コンテンツ追加（動画・画像・音声に対応）
# ===============================
#フロント側ではテキスト投稿以外はfile,thumbnailを指定する。テキスト投稿の場合はtextにデータを含める
@content_bp.route("/add", methods=["POST"])
@jwt_required
def add_content():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()

        # --- 受信データ ---
        content_type = data.get("type")      # "video" | "image" | "audio" | "text"
        title = data.get("title")
        link = data.get("link")

        if content_type != "text":

            file_data = data.get("file")         # base64文字列（コンテンツ本体）
            thumb_data = data.get("thumbnail")   # base64文字列（サムネイル）
            if not all([content_type, title, file_data, thumb_data]):
                return jsonify({
                    "status": "error",
                    "message": "必要なデータが不足しています"
                }), 400

            # --- パス設定 ---
            base_dir = os.path.join(current_app.root_path, "content")
            subdirs = {
                "video": "movie",
                "image": "picture",
                "audio": "audio",
                "thumbnail": "thumbnail"
            }
            for sub in subdirs.values():
                os.makedirs(os.path.join(base_dir, sub), exist_ok=True)

            # --- ファイル名作成 ---
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename_base = f"{uid}_{timestamp}"

            # --- ファイル拡張子設定 ---
            ext_map = {"video": "mp4", "image": "jpg", "audio": "mp3"}
            ext = ext_map.get(content_type, "dat")

            # --- ファイル保存 ---
            content_rel_path = f"content/{subdirs[content_type]}/{filename_base}.{ext}"
            thumb_rel_path = f"content/thumbnail/{filename_base}_thumb.jpg"

            content_abs_path = os.path.join(current_app.root_path, content_rel_path)
            thumb_abs_path = os.path.join(current_app.root_path, thumb_rel_path)

            # Base64 → バイナリ書き込み
            with open(content_abs_path, "wb") as f:
                f.write(base64.b64decode(file_data))

            with open(thumb_abs_path, "wb") as f:
                f.write(base64.b64decode(thumb_data))

            # --- DB登録 ---
            content_id = add_content_and_link_to_users(
                contentpath=content_rel_path,
                thumbnailpath=thumb_rel_path,
                link=link,
                title=title,
                userID=uid
            )
        else:
            text = data.get("text") 
            #--- DB登録(text) ---
            content_id = add_content_and_link_to_users(
                contentpath=text,
                link=link,
                title=title,
                userID=uid,
                textflag="TRUE"
            )

        return jsonify({
            "status": "success",
            "message": "コンテンツを追加しました。",
            "data": {
                "contentID": content_id,
                "contentpath": content_rel_path,
                "thumbnailpath": thumb_rel_path
            }
        }), 200

    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400

# ===============================
# 2️⃣ コメント追加
# ===============================
#フロント側ではコメントに対する返信ではない場合parentcommentidはbodyに含めない
@content_bp.route('/addcomment', methods=['POST'])
@jwt_required
def add_comment():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        parentcommentid = data.get("parentcommentID")
        if parentcommentid:
            insert_comment(
                userID=uid,
                commenttext=data.get("commenttext")
            )
        else:
            insert_comment(
                userID=uid,
                commenttext=data.get("commenttext"),
                parentcommentID=parentcommentid
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
        uid = request.user["firebase_uid"]
        data = request.get_json()
        contentID = data.get("contentID")
        nextcontentID = get_play_content_id(contentID)
        if not nextcontentID:
            return jsonify({"status": "error", "message": "読み込み可能なコンテンツがありません"}), 200
        detail = get_content_detail(nextcontentID)
        # if not detail:
        #     return jsonify({"status": "error", "message": "コンテンツが見つかりません"}), 404

        spotlightflag = get_user_spotlight_flag(uid,nextcontentID)
        insert_play_history(userID=uid,contentID=nextcontentID)
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
                "iconimgpath": detail[7],
                "spotlightflag": spotlightflag,
                "textflag":detail[8],
                "nextcontentid": nextcontentID
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
        data = request.get_json()
        contentID = data.get("contentID")
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
        data = request.get_json()
        contentID = data.get("contentID")
        spotlight_off(contentID, uid)
        return jsonify({"status": "success", "message": "スポットライトをOFFにしました"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 5️⃣ コンテンツのコメント一覧を取得
# ===============================
@content_bp.route('/getcomments', methods=['POST'])
@jwt_required
def get_comments():
    try:
        data = request.get_json()
        content_id = data.get("contentID")

        if not content_id:
            return jsonify({"status": "error", "message": "contentIDが指定されていません"}), 400

        rows = get_comments_by_content(content_id)

        # コメントを辞書リストに変換
        comments = [
            {
                "commentID": row[0],
                "username": row[1],
                "iconimgpath": row[2],
                "commenttimestamp": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None,
                "commenttext": row[4],
                "parentcommentID": row[5],
                "replies": []  # 返信格納用
            }
            for row in rows
        ]

        # === スレッド構造に整形 ===
        comment_dict = {c["commentID"]: c for c in comments}
        root_comments = []

        for c in comments:
            parent_id = c["parentcommentID"]
            if parent_id and parent_id in comment_dict:
                comment_dict[parent_id]["replies"].append(c)
            else:
                root_comments.append(c)

        return jsonify({
            "status": "success",
            "data": root_comments  # 親コメントをルートにしたツリー構造
        }), 200

    except Exception as e:
        print("⚠️エラー(get_comments):", e)
        return jsonify({"status": "error", "message": str(e)}), 400



#プレイリスト作成
@content_bp.route('/createplaylist', methods=['POST'])
@jwt_required
def create_playlist():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        title = data.get("title")
        insert_playlist(uid, title)
        return jsonify({"status": "success", "message": "プレイリストを作成しました"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400

#プレイリストにコンテンツ追加
@content_bp.route('/addcontentplaylist', methods=['POST'])
@jwt_required
def add_content_in_playlist():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        playlistid = data.get("playlistid")
        contentid = data.get("playlistid")
        insert_playlist_detail(uid, playlistid, contentid)
        return jsonify({"status": "success", "message": "プレイリストにコンテンツを追加しました"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400



#プレイリスト一覧を取得
@content_bp.route('/getplaylist', methods=['POST'])
@jwt_required
def get_playlist():
    try:
        uid = request.user["firebase_uid"]
        result = get_playlists_with_thumbnail(uid)
        return jsonify({"status": "success", "playlist": result}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


#プレイリストのコンテンツ一覧を取得
@content_bp.route('/getplaylistdetail', methods=['POST'])
@jwt_required
def get_playlistdetail():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        playlistid = data.get("playlistid")
        rows = get_playlist_contents(uid,playlistid)

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
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400

#検索機能
@content_bp.route('/serch', methods=['POST'])
@jwt_required
def serch():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        serchword = data.get("word")
        #検索履歴を保存
        insert_search_history(userID=uid,serchword=serchword)

        # モデル関数から検索結果を取得
        rows = get_search_contents(serchword)

        # データが存在しない場合
        if not rows:
            return jsonify({"status": "success", "message": "該当するコンテンツがありません", "data": []}), 200

        # Dartで扱いやすいように整形
        result = []
        for row in rows:
            result.append({
                "contentID": row[0],
                "title": row[1],
                "spotlightnum": row[2],
                "posttimestamp": row[3],
                "playnum": row[4],
                "link": row[5],
                "thumbnailurl": row[6]
            })

        return jsonify({
            "status": "success",
            "message": f"{len(result)}件のコンテンツが見つかりました。",
            "data": result
        }), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400
        