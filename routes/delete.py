from utils.auth import jwt_required
from models.deletedata import (
    delete_play_history, delete_playlist_detail, delete_playlist,
    delete_serch_history, delete_notification, delete_comment, delete_content
)
from models.selectdata import get_user_name_iconpath, get_content_detail, get_search_history
from flask import Blueprint, request, jsonify

delete_bp = Blueprint('delete_bp', __name__, url_prefix='/api/delete')

# ========================================
# ヘルパー関数：タイトルを15文字に制限
# ========================================
def truncate_title(title, max_length=15):
    """
    タイトルを最大15文字に制限
    
    Args:
        title: タイトル文字列
        max_length: 最大文字数（デフォルト15）
    
    Returns:
        str: 制限されたタイトル
    """
    if not title:
        return ""
    if len(title) <= max_length:
        return title
    return title[:max_length]


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
        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"再生履歴削除:{username}")

        return success("視聴履歴を削除しました")

    except Exception as e:
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
        username, _, _, _ = get_user_name_iconpath(uid)
        # 投稿タイトルを取得
        detail = get_content_detail(contentid)
        if detail:
            content_title = detail[0]
            print(f"プレイリストから削除:{username}:\"{truncate_title(content_title)}\"")

        return success("プレイリスト内のコンテンツを削除しました")

    except Exception as e:
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
        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"プレイリスト削除:{username}")

        return success("プレイリストを削除しました")

    except Exception as e:
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
        username, _, _, _ = get_user_name_iconpath(uid)
        # serchidは実際には検索ワード
        print(f"検索履歴削除:{username}:{serchid}")

        return success("検索履歴を削除しました")

    except Exception as e:
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
        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"通知削除:{username}")

        return success("通知を削除しました")

    except Exception as e:
        return error(str(e))


# ===========================================
# 6. コメント削除
# ===========================================
@delete_bp.route("/comment", methods=["POST"])
@jwt_required
def delete_comment_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}

        contentid = data.get("contentID")
        commentid = data.get("commentID")

        if contentid is None or commentid is None:
            return error("contentID と commentID が必要です")

        delete_comment(contentid, commentid)
        # 投稿タイトルを取得
        detail = get_content_detail(contentid)
        if detail:
            content_title = detail[0]
            username, _, _, _ = get_user_name_iconpath(uid)
            print(f"コメント削除:{username}:\"{truncate_title(content_title)}\"")

        return success("コメントを削除しました")

    except Exception as e:
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
        username, _, _, _ = get_user_name_iconpath(uid)
        # 投稿タイトルを取得
        detail = get_content_detail(contentid)
        if detail:
            content_title = detail[0]
            print(f"投稿削除:{username}:\"{truncate_title(content_title)}\"")

        return success("コンテンツを削除しました")

    except Exception as e:
        return error(str(e))
