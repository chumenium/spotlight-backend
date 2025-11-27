from utils.auth import jwt_required
from models.deletedata import (
    delete_play_history, delete_playlist_detail, delete_playlist,
    delete_serch_history, delete_notification, delete_comment, delete_content
)
from flask import Blueprint, request, jsonify

delete_bp = Blueprint('content', __name__, url_prefix='/api/delete')


# 共通レスポンス関数
def success(message):
    return jsonify({"status": "success", "message": message}), 200

def error(message):
    return jsonify({"status": "error", "message": message}), 400


# ===========================================
# 1. 視聴履歴削除
# ===========================================
@delete_bp.route("/playhistory", methods=["POST"])
@jwt_required
def delete_play_history_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}
        playid = data.get("playID")

        if playid is None:
            return error("playID が必要です")

        delete_play_history(uid, playid)
        print(f"🗑️ 視聴履歴削除: uid={uid}, playID={playid}")

        return success("視聴履歴を削除しました")

    except Exception as e:
        print("⚠️ エラー(delete_playhistory):", e)
        return error(str(e))


# ===========================================
# 2. プレイリストの中身から削除
# ===========================================
@delete_bp.route("/playlistdetail", methods=["POST"])
@jwt_required
def delete_playlist_detail_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}

        playlistid = data.get("playlistID")
        contentid = data.get("contentID")

        if playlistid is None or contentid is None:
            return error("playlistID と contentID が必要です")

        delete_playlist_detail(uid, playlistid, contentid)
        print(f"🗑️ プレイリスト内削除: uid={uid}, playlistID={playlistid}, contentID={contentid}")

        return success("プレイリスト内のコンテンツを削除しました")

    except Exception as e:
        print("⚠️ エラー(delete_playlist_detail):", e)
        return error(str(e))


# ===========================================
# 3. プレイリスト削除
# ===========================================
@delete_bp.route("/playlist", methods=["POST"])
@jwt_required
def delete_playlist_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}

        playlistid = data.get("playlistID")

        if playlistid is None:
            return error("playlistID が必要です")

        delete_playlist(uid, playlistid)
        print(f"🗑️ プレイリスト削除: uid={uid}, playlistID={playlistid}")

        return success("プレイリストを削除しました")

    except Exception as e:
        print("⚠️ エラー(delete_playlist):", e)
        return error(str(e))


# ===========================================
# 4. 検索履歴削除
# ===========================================
@delete_bp.route("/searchhistory", methods=["POST"])
@jwt_required
def delete_search_history_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}

        serchid = data.get("serchID")

        if serchid is None:
            return error("serchID が必要です")

        delete_serch_history(uid, serchid)
        print(f"🗑️ 検索履歴削除: uid={uid}, serchID={serchid}")

        return success("検索履歴を削除しました")

    except Exception as e:
        print("⚠️ エラー(delete_searchhistory):", e)
        return error(str(e))


# ===========================================
# 5. 通知削除
# ===========================================
@delete_bp.route("/notification", methods=["POST"])
@jwt_required
def delete_notification_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}

        notificationid = data.get("notificationID")

        if notificationid is None:
            return error("notificationID が必要です")

        delete_notification(uid, notificationid)
        print(f"🗑️ 通知削除: uid={uid}, notificationID={notificationid}")

        return success("通知を削除しました")

    except Exception as e:
        print("⚠️ エラー(delete_notification):", e)
        return error(str(e))


# ===========================================
# 6. コメント削除
# ===========================================
@delete_bp.route("/comment", methods=["POST"])
@jwt_required
def delete_comment_api():
    try:
        data = request.get_json() or {}

        contentid = data.get("contentID")
        commentid = data.get("commentID")

        if contentid is None or commentid is None:
            return error("contentID と commentID が必要です")

        delete_comment(contentid, commentid)
        print(f"🗑️ コメント削除: contentID={contentid}, commentID={commentid}")

        return success("コメントを削除しました")

    except Exception as e:
        print("⚠️ エラー(delete_comment):", e)
        return error(str(e))


# ===========================================
# 7. コンテンツ削除
# ===========================================
@delete_bp.route("/content", methods=["POST"])
@jwt_required
def delete_content_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}

        contentid = data.get("contentID")

        if contentid is None:
            return error("contentID が必要です")

        delete_content(uid, contentid)
        print(f"🗑️ コンテンツ削除: uid={uid}, contentID={contentid}")

        return success("コンテンツを削除しました")

    except Exception as e:
        print("⚠️ エラー(delete_content):", e)
        return error(str(e))
