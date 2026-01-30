"""
コンテンツ管理API
"""
# from turtle import title
from flask import Blueprint, request, jsonify
from utils.auth import jwt_required, debounce_request

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

# ========================================
# ヘルパー関数：コンテンツタイプを推測
# ========================================
def infer_content_type(contentpath, textflag):
    """
    contentpathとtextflagからコンテンツタイプを推測
    
    Args:
        contentpath: コンテンツパス（URLまたはパス）
        textflag: テキストフラグ
    
    Returns:
        str: "video", "image", "audio", "text"
    """
    if textflag:
        return "text"
    
    if not contentpath:
        return "text"
    
    contentpath_lower = contentpath.lower()
    
    # 動画の判定
    if "/movie/" in contentpath_lower or \
       contentpath_lower.endswith((".mp4", ".mov", ".avi", ".webm")):
        return "video"
    
    # 画像の判定
    if "/picture/" in contentpath_lower or \
       contentpath_lower.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return "image"
    
    # 音声の判定
    if "/audio/" in contentpath_lower or \
       contentpath_lower.endswith((".mp3", ".wav", ".m4a", ".aac")):
        return "audio"
    
    # デフォルトはテキスト
    return "text"

from models.updatedata import spotlight_on, spotlight_off, add_playnum, update_content_title_tag
from models.selectdata import (
    get_content_detail,get_user_spotlight_flag,get_comments_by_content,get_play_content_id,
    get_search_contents, get_playlists_with_thumbnail, get_playlist_contents, get_user_name_iconpath,
    get_user_by_content_id, get_user_by_id, get_user_by_parentcomment_id, get_comment_num, get_notified,get_blocked_users
)
from models.createdata import (
    add_content_and_link_to_users, insert_comment, insert_playlist, insert_playlist_detail,
    insert_search_history, insert_play_history, insert_notification
)
from models.content_get import(
        update_last_contetid, get_content_random_5, get_content_id_range
)
from utils.notification import send_push_notification

import base64
import os
from datetime import datetime
from flask import current_app
from utils.s3 import upload_to_s3, get_cloudfront_url, get_content_type_from_extension, normalize_content_url


content_bp = Blueprint('content', __name__, url_prefix='/api/content')

def clean_base64(b64_string):
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]
    return b64_string


import subprocess
import tempfile

MAX_BITRATE = 6000 * 1000  # 7000kbps = 7,000,000 bps

def get_video_bitrate(file_path):
    """ffprobeで動画ビットレートを取得"""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=bit_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        bitrate = int(result.stdout.strip())
        return bitrate
    except:
        return None


def compress_video_if_needed(file_binary, max_bitrate=MAX_BITRATE):
    """ビットレートが高い場合は7000kbpsに再エンコード"""
    # 一時ファイル作成
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
        tmp_in.write(file_binary)
        input_path = tmp_in.name

    output_path = input_path + "_compressed.mp4"

    # 現在のビットレート取得
    bitrate = get_video_bitrate(input_path)

    if bitrate and bitrate > max_bitrate:

        # ffmpegで7000kbpsに変換
        cmd = [
            "ffmpeg", "-i", input_path,
            "-b:v", f"{max_bitrate}",
            "-bufsize", f"{max_bitrate}",
            "-maxrate", f"{max_bitrate}",
            "-preset", "medium",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 変換後ファイルを読み込み
        with open(output_path, "rb") as f:
            new_binary = f.read()
        # 一時ファイル削除
        os.remove(input_path)
        os.remove(output_path)

        return new_binary  # 変換後バイナリを返す

    # 変換不要なら元のバイナリ返す
    os.remove(input_path)
    return file_binary


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
        username, iconimgpath, admin, _ = get_user_name_iconpath(uid)

        # --- 受信データ ---
        content_type = data.get("type")      # "video" | "image" | "audio" | "text"
        title = data.get("title")
        link = data.get("link")
        tag = data.get("tag")
        # デバッグ用のprint文を削除（コスト削減のため）
        if not(tag == None):
            tag = tag.replace("#", "")
        if content_type != "text":

            file_data = data.get("file")         # base64文字列（コンテンツ本体）
            thumb_data = data.get("thumbnail")   # base64文字列（サムネイル）
            file_data = clean_base64(file_data)
            thumb_data = clean_base64(thumb_data)
            if not all([content_type, title, file_data, thumb_data]):
                return jsonify({
                    "status": "error",
                    "message": "必要なデータが不足しています"
                }), 400

            # --- フォルダマッピング ---
            subdirs = {
                "video": "movie",
                "image": "picture",
                "audio": "audio",
                "thumbnail": "thumbnail"
            }

            # --- ファイル名作成 ---
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename_base = f"{username}_{timestamp}"

            # --- ファイル拡張子設定 ---
            ext_map = {"video": "mp4", "image": "jpg", "audio": "mp3"}
            ext = ext_map.get(content_type, "dat")

            # --- ファイル名 ---
            content_filename = f"{filename_base}.{ext}"
            thumb_filename = f"{filename_base}_thumb.jpg"

            # --- Base64 → バイナリ変換 ---
            content_binary = base64.b64decode(file_data)
            thumb_binary = base64.b64decode(thumb_data)
            
            # ★★ 動画の場合はビットレートチェック & 圧縮する
            # if content_type == "video":
            #     content_binary = compress_video_if_needed(content_binary)

            # --- S3にアップロード ---
            content_folder = subdirs[content_type]
            content_bucket = None  # デフォルトバケット（spotlight-contents）を使用
            content_mime = get_content_type_from_extension(content_type, ext)
            
            # コンテンツ本体をS3にアップロード
            content_key = upload_to_s3(
                file_data=content_binary,
                folder=content_folder,
                filename=content_filename,
                content_type=content_mime,
                bucket_name=content_bucket
            )

            # サムネイルをS3にアップロード
            thumb_key = upload_to_s3(
                file_data=thumb_binary,
                folder="thumbnail",
                filename=thumb_filename,
                content_type="image/jpeg"
            )

            # --- CloudFront URL生成 ---
            content_url = get_cloudfront_url(content_folder, content_filename)
            thumb_url = get_cloudfront_url("thumbnail", thumb_filename)

            # --- DB登録（CloudFront URLを保存） ---
            content_id = add_content_and_link_to_users(
                contentpath=content_url,
                thumbnailpath=thumb_url,
                link=link,
                title=title,
                userID=uid,
                tag=tag
            )
            print(f"投稿作成:{username}:\"{truncate_title(title)}\"")
        else:
            text = data.get("text") 
            #--- DB登録(text) ---
            content_id = add_content_and_link_to_users(
                contentpath=text,
                link=link,
                title=title,
                userID=uid,
                textflag="TRUE",
                tag=tag
            )
            print(f"投稿作成:{username}:\"{truncate_title(title)}\"")

        if content_type != "text":
            return jsonify({
                "status": "success",
                "message": "コンテンツを追加しました。",
                "data": {
                    "contentID": content_id,
                    "contentpath": content_url,
                    "thumbnailpath": thumb_url
                }
            }), 200
        else:
            return jsonify({
                "status": "success",
                "message": "コンテンツを追加しました。",
                "data": {
                    "contentID": content_id
                }
            }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 1.5️⃣ 自分の投稿を編集（タイトル・タグ）
# ===============================
@content_bp.route("/edit", methods=["PATCH", "PUT"])
@jwt_required
def edit_content():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}
        contentID = data.get("contentID")
        if contentID is None:
            return jsonify({"status": "error", "message": "contentIDが指定されていません"}), 400
        if "title" not in data and "tag" not in data:
            return jsonify({"status": "error", "message": "title または tag のいずれかは指定してください"}), 400

        content_user = get_user_by_content_id(contentID)
        if not content_user:
            return jsonify({"status": "error", "message": "投稿が見つかりません"}), 404
        if content_user["userID"] != uid:
            return jsonify({"status": "error", "message": "自分の投稿のみ編集できます"}), 403

        title = data.get("title") if "title" in data else None
        tag = data.get("tag") if "tag" in data else None
        if tag is not None:
            tag = tag.replace("#", "")

        ok = update_content_title_tag(contentID, uid, title=title, tag=tag)
        if not ok:
            return jsonify({"status": "error", "message": "更新に失敗しました"}), 500

        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"投稿編集:{username}:contentID={contentID}")
        return jsonify({"status": "success", "message": "投稿を更新しました"}), 200
    except Exception as e:
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
        contentID = data.get("contentID")
        user_data = get_user_by_id(uid)
        post_username = user_data["username"]
        commenttext = data.get("commenttext")
        if parentcommentid:
            commentid = insert_comment(
                contentID=contentID,
                userID=uid,
                commenttext=commenttext,
                parentcommentID=parentcommentid
            )
            #投稿もとのコメント主に通知を送信
            posted_by_user_data = get_user_by_parentcomment_id(contentID, parentcommentid)
            if posted_by_user_data["notificationenabled"]:
                if uid != posted_by_user_data["userID"]:
                    send_push_notification(posted_by_user_data["token"], post_username+"さんが返信を投稿",commenttext)
            if uid != posted_by_user_data["userID"]:
                insert_notification(userID=posted_by_user_data["userID"],comCTID=contentID,comCMID=commentid)
        else:
            commentid = insert_comment(
                contentID=contentID,
                userID=uid,
                commenttext=commenttext,
            )
            #投稿元のユーザに通知を送信
            content_user_data = get_user_by_content_id(contentID)
            content_title = content_user_data["title"]
            if content_user_data["notificationenabled"]:
                if uid != content_user_data["userID"]:
                    send_push_notification(content_user_data["token"], post_username+"さんがコメントを投稿",content_title+":"+commenttext)
            if uid != content_user_data["userID"]:
                insert_notification(userID=content_user_data['userID'],comCTID=contentID,comCMID=commentid)
                notified_username, _, _, _ = get_user_name_iconpath(content_user_data['userID'])
                print(f"通知:{notified_username}:通知種別(コメント)")
            print(f"コメント投稿:{post_username}:\"{truncate_title(content_title)}\"")

        return jsonify({"status": "success", "message": "コメントを追加しました。"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# # ===============================
# # 3️⃣ コンテンツ読み込み ・視聴履歴、自分の投稿取得
# # ===============================
@content_bp.route('/detail', methods=['POST'])
@jwt_required
@debounce_request(ttl=0.5)  # 0.5秒以内の重複リクエストを無視
def content_detail():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}
        contentID = data.get("contentID")
        
        # contentIDが指定されていない場合はデータベースからランダムなコンテンツを取得
        if contentID is None:
            from models.selectdata import get_random_content_id
            
            # データベースからランダムなcontentIDを取得（S3への直接アクセスを避ける）
            nextcontentID = get_random_content_id()
            
            if not nextcontentID:
                return jsonify({"status": "error", "message": "読み込み可能なコンテンツがありません"}), 200
            
            # データベースからコンテンツ詳細を取得
            detail = get_content_detail(nextcontentID)
            if not detail:
                return jsonify({"status": "error", "message": "コンテンツが見つかりません"}), 404
        else:
            # 指定されたcontentIDを使用（後方互換性のため）
            nextcontentID = contentID
            detail = get_content_detail(nextcontentID)
            if not detail:
                return jsonify({"status": "error", "message": "コンテンツが見つかりません"}), 404
        

        # nextcontentIDがNoneの場合はspotlightflagをFalseに設定
        if nextcontentID is not None:
            spotlightflag = get_user_spotlight_flag(uid, nextcontentID)
        else:
            spotlightflag = False
        
        # DBから取得したパスをCloudFront URLに正規化（既存データの互換性のため）
        contentpath = normalize_content_url(detail[1]) if detail[1] else None
        thumbnailpath = normalize_content_url(detail[9]) if len(detail) > 9 and detail[9] else None
        
        # デバッグ用のprint文を削除（コスト削減のため）
        commentnum = get_comment_num(nextcontentID)
        
        # アイコンパスをCloudFront URLに正規化
        iconimgpath = normalize_content_url(detail[7]) if len(detail) > 7 and detail[7] else None
        
        # 投稿取得ログ
        username, _, _, _ = get_user_name_iconpath(uid)
        content_title = detail[0]
        print(f"投稿取得:{username}:\"{truncate_title(content_title)}\"")
        
        return jsonify({
            "status": "success",
            "data": {
                "title": detail[0],
                "contentpath": contentpath,
                "thumbnailpath": thumbnailpath,
                "spotlightnum": detail[2],
                "posttimestamp": detail[3].isoformat(),
                "playnum": detail[4],
                "link": detail[5],
                "username": detail[6],
                "iconimgpath": iconimgpath,
                "spotlightflag": spotlightflag,
                "textflag":detail[8],
                "nextcontentid": nextcontentID,
                "commentnum":commentnum
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


#===============================
#再生回数追加+再生履歴の追加
#===============================
@content_bp.route('/playnum', methods=['POST'])
@jwt_required
def playnum_add_route():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        contentID = data.get("contentID")
        
        if not contentID:
            return jsonify({"status": "error", "message": "contentIDが指定されていません"}), 400
        
        add_playnum(contentID)
        insert_play_history(userID=uid, contentID=contentID)
        # 投稿タイトルを取得
        detail = get_content_detail(contentID)
        if detail:
            content_title = detail[0]
            username, _, _, _ = get_user_name_iconpath(uid)
            print(f"再生:{username}:\"{truncate_title(content_title)}\"")
        return jsonify({"status": "success", "message": "再生回数を追加"}), 200
    except Exception as e:
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
        #投稿元のユーザに通知を送信
        content_user_data = get_user_by_content_id(contentID)
        spotlight_user = get_user_by_id(uid)  # if文の外で定義
        content_title = content_user_data["title"]
        if content_user_data["notificationenabled"]:
            if uid != content_user_data["userID"]:
                #スポットライトオンオフを連打しても通知を一度だけにする
                isnotififlag = get_notified(contentid=contentID, uid=content_user_data["userID"])
                if not isnotififlag:
                    send_push_notification(content_user_data["token"], "スポットライトが当てられました",content_title+"に"+spotlight_user["username"]+"さんがスポットライトを当てました")
        if  uid != content_user_data["userID"]:
            insert_notification(userID=content_user_data["userID"],contentuserCID=contentID,contentuserUID=spotlight_user["userID"])
            notified_username, _, _, _ = get_user_name_iconpath(content_user_data["userID"])
            print(f"通知:{notified_username}:通知種別(スポットライト)")
        print(f"スポットライト:{spotlight_user['username']}:\"{truncate_title(content_title)}\"")
        return jsonify({"status": "success", "message": "スポットライトをONにしました"}), 200
    except Exception as e:
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
        # 投稿タイトルを取得
        content_user_data = get_user_by_content_id(contentID)
        spotlight_user = get_user_by_id(uid)
        content_title = content_user_data["title"]
        print(f"スポットライト解除:{spotlight_user['username']}:\"{truncate_title(content_title)}\"")
        return jsonify({"status": "success", "message": "スポットライトをOFFにしました"}), 200
    except Exception as e:
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
        uid = request.user["firebase_uid"]

        if not content_id:
            return jsonify({"status": "error", "message": "contentIDが指定されていません"}), 400

        rows = get_comments_by_content(content_id)
        blocked_users = get_blocked_users(uid)

        # ブロックしたユーザーのusernameのセットを作成
        blocked_usernames = {blocked_user[1] for blocked_user in blocked_users} if blocked_users else set()

        # コメントを辞書リストに変換
        comments = [
            {
                "commentID": row[0],
                "username": row[1],
                "iconimgpath": normalize_content_url(row[2]) if len(row) > 2 and row[2] else None,
                "commenttimestamp": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None,
                "commenttext": row[4],
                "parentcommentID": row[5],
                "replies": []  # 返信格納用
            }
            for row in rows
        ]

        # ブロックしたユーザーのコメントを除外
        # ブロックしたユーザーのコメントIDを記録（子コメントも除外するため）
        blocked_comment_ids = set()
        filtered_comments = []
        
        for c in comments:
            # ブロックしたユーザーのコメントを除外
            if c["username"] in blocked_usernames:
                blocked_comment_ids.add(c["commentID"])
                continue
            filtered_comments.append(c)

        # ブロックしたユーザーのコメントに対する子コメント（返信）も除外
        # また、ブロックしたユーザーが書いた子コメントも除外
        final_comments = []
        for c in filtered_comments:
            parent_id = c["parentcommentID"]
            # 親コメントがブロックされたコメントの場合は除外
            if parent_id and parent_id in blocked_comment_ids:
                continue
            final_comments.append(c)

        # === スレッド構造に整形 ===
        comment_dict = {c["commentID"]: c for c in final_comments}
        root_comments = []

        for c in final_comments:
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
        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"プレイリスト作成:{username}")
        return jsonify({"status": "success", "message": "プレイリストを作成しました"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

#プレイリストにコンテンツ追加
@content_bp.route('/addcontentplaylist', methods=['POST'])
@jwt_required
def add_content_in_playlist():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        playlistid = data.get("playlistID")
        contentid = data.get("contentID")
        insert_playlist_detail(uid, playlistid, contentid)
        username, _, _, _ = get_user_name_iconpath(uid)
        # 投稿タイトルを取得
        detail = get_content_detail(contentid)
        if detail:
            content_title = detail[0]
            print(f"プレイリスト追加:{username}:\"{truncate_title(content_title)}\"")
        return jsonify({"status": "success", "message": "プレイリストにコンテンツを追加しました"}), 200
    except Exception as e:
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
                "thumbnailpath": normalize_content_url(row[6]) if len(row) > 6 and row[6] else None,
            }
            for row in rows
        ]

        return jsonify({"status": "success", "data": contents}), 200
    except Exception as e:
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
        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"検索:{username}:{serchword}")

        # モデル関数から検索結果を取得
        rows = get_search_contents(serchword, uid)

        # データが存在しない場合
        if not rows:
            return jsonify({"status": "success", "message": "該当するコンテンツがありません", "data": []}), 200

        # Dartで扱いやすいように整形（視聴履歴APIと同じ形式で posttimestamp を文字列化）
        result = []
        for row in rows:
            thumbnailurl = normalize_content_url(row[6]) if len(row) > 6 and row[6] else None
            username = row[7] if len(row) > 7 else ''
            iconimgpath = row[8] if len(row) > 8 else ''
            pt = row[3]
            posttimestamp = pt.strftime("%Y-%m-%d %H:%M:%S") if pt else None
            result.append({
                "contentID": row[0],
                "title": row[1],
                "spotlightnum": row[2],
                "posttimestamp": posttimestamp,
                "playnum": row[4],
                "link": row[5],
                "thumbnailurl": thumbnailurl,
                "username": username,
                "iconimgpath": iconimgpath or '',
            })

        return jsonify({
            "status": "success",
            "message": f"{len(result)}件のコンテンツが見つかりました。",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
        

# #コンテンツのランダム取得API
# @content_bp.route('/getcontents', methods=['POST'])
# @jwt_required
# @debounce_request(ttl=2.0)  # 2秒以内の重複リクエストを無視（スクロール中の重複取得を防ぐ）
# def get_content_random_5():
#     try:
#         uid = request.user["firebase_uid"]
#         data = request.get_json() or {}
#         # スクロール中の重複取得を防ぐため、既に取得したコンテンツIDを除外
#         exclude_content_ids = data.get("excludeContentIDs", [])
        
#         rows = get_recent_history_ids(uid, exclude_content_ids=exclude_content_ids)
#         lastcontentid = None
#         # Dartで扱いやすいように整形
#         result = []
#         # 既に取得したcontentIDを追跡（重複防止用）
#         fetched_content_ids = set()

#         for row in rows:
#             content_id = row[13]
#             # 重複チェック
#             if content_id in fetched_content_ids:
#                 continue
#             fetched_content_ids.add(content_id)
            
#             # DBから取得したパスをCloudFront URLに正規化
#             contentpath = normalize_content_url(row[1]) if row[1] else None
#             thumbnailpath = normalize_content_url(row[10]) if len(row) > 10 and row[10] else None
#             iconimgpath = normalize_content_url(row[8]) if len(row) > 8 and row[8] else None
#             result.append({
#                 "title": row[0],
#                 "contentpath": contentpath,
#                 "thumbnailpath": thumbnailpath,
#                 "spotlightnum": row[2],
#                 "posttimestamp": row[3].isoformat(),
#                 "playnum": row[4],
#                 "link": row[5],
#                 "username": row[6],
#                 "user_id": row[7],  # userIDを追加
#                 "iconimgpath": iconimgpath,
#                 "spotlightflag": row[11],
#                 "textflag":row[9],
#                 "commentnum":row[12],
#                 "contentID":row[13]
#             })
#             lastcontentid = row[13]
#         # printtext = "ランダム取得したコンテンツ"
#         # for i in range(len(result)):
#         #     printtext += str(result[i]["contentID"]) + ":" +str(result[i]["title"]) +","
#         # print(printtext)

#         resultnum = len(result)
#         shortagenum = 5 - resultnum
#         # 不足分がある場合、既に取得したcontentIDを除外して追加取得
#         while shortagenum > 0:
#             rows2 = get_history_ran(uid, limitnum=shortagenum, exclude_content_ids=list(fetched_content_ids))
#             if not rows2:
#                 # これ以上取得できるコンテンツがない場合
#                 break
            
#             for row in rows2:
#                 content_id = row[13]
#                 # 重複チェック（念のため）
#                 if content_id in fetched_content_ids:
#                     continue
#                 fetched_content_ids.add(content_id)
                
#                 # DBから取得したパスをCloudFront URLに正規化
#                 contentpath = normalize_content_url(row[1]) if row[1] else None
#                 thumbnailpath = normalize_content_url(row[10]) if len(row) > 10 and row[10] else None
#                 iconimgpath = normalize_content_url(row[8]) if len(row) > 8 and row[8] else None
                
#                 # コンテンツタイプを推測
#                 content_type = infer_content_type(contentpath, row[9])
                
#                 result.append({
#                     "title": row[0],
#                     "contentpath": contentpath,
#                     "thumbnailpath": thumbnailpath,
#                     "type": content_type,
#                     "spotlightnum": row[2],
#                     "posttimestamp": row[3].isoformat(),
#                     "playnum": row[4],
#                     "link": row[5],
#                     "username": row[6],
#                     "user_id": row[7],  # userIDを追加
#                     "iconimgpath": iconimgpath,
#                     "spotlightflag": row[11],
#                     "textflag":row[9],
#                     "commentnum":row[12],
#                     "contentID":row[13]
#                 })
#                 lastcontentid = row[13]
#                 shortagenum -= 1

#                 # 5件取得できたら終了
#                 if len(result) >= 5:
#                     break
#             # デバッグ用のprint文を削除（コスト削減のため）
#             # 5件取得できたか、これ以上取得できない場合は終了
#             if len(result) >= 5 or not rows2:
#                 break
        
#         if lastcontentid:
#             update_last_contetid(uid, lastcontentid)

#         return jsonify({
#             "status": "success",
#             "message": f"{len(result)}件のコンテンツを取得",
#             "data": result
#         }), 200
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 400





# ========================================
# 完全ランダム取得API（ループ対応）　・ホーム画面取得
# ========================================
@content_bp.route('/getcontents/random', methods=['POST'])
@jwt_required
@debounce_request(ttl=3.0)  # 3秒以内の重複リクエストを無視（スクロール中の重複取得を防ぐ）
def get_content_random_api():
    """
    完全ランダムで3件取得（重複なし、ループ対応）
    最後まで行ったら最初に戻る
    """
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}
        exclude_content_ids = data.get("excludeContentIDs", [])  # フロントから除外IDリストを受け取る
        
        # ランダムで3件取得
        rows = get_content_random_5(uid, exclude_content_ids=exclude_content_ids)
        
        result = []
        fetched_content_ids = set()
        min_content_id = None
        max_content_id = None
        
        for row in rows:
            content_id = row[13]
            if content_id in fetched_content_ids:
                continue
            fetched_content_ids.add(content_id)
            
            # 最小・最大IDを記録（ループ判定用）
            if min_content_id is None or content_id < min_content_id:
                min_content_id = content_id
            if max_content_id is None or content_id > max_content_id:
                max_content_id = content_id
            
            # DBから取得したパスをCloudFront URLに正規化
            contentpath = normalize_content_url(row[1]) if row[1] else None
            thumbnailpath = normalize_content_url(row[10]) if len(row) > 10 and row[10] else None
            iconimgpath = normalize_content_url(row[8]) if len(row) > 8 and row[8] else None
            
            # コンテンツタイプを推測
            content_type = infer_content_type(contentpath, row[9])
            
            result.append({
                "title": row[0],
                "contentpath": contentpath,
                "thumbnailpath": thumbnailpath,
                "type": content_type,
                "spotlightnum": row[2],
                "posttimestamp": row[3].isoformat(),
                "playnum": row[4],
                "link": row[5],
                "username": row[6],
                "user_id": row[7],
                "iconimgpath": iconimgpath,
                "spotlightflag": row[11],
                "textflag": row[9],
                "commentnum": row[12],
                "contentID": row[13]
            })
        
        # 不足分がある場合、ループして最初から取得
        if len(result) < 3:
            # 既に取得したIDを除外して追加取得
            additional_exclude = list(fetched_content_ids) + exclude_content_ids
            additional_rows = get_content_random_5(uid, exclude_content_ids=additional_exclude)
            
            for row in additional_rows:
                if len(result) >= 3:
                    break
                content_id = row[13]
                if content_id in fetched_content_ids:
                    continue
                fetched_content_ids.add(content_id)
                
                contentpath = normalize_content_url(row[1]) if row[1] else None
                thumbnailpath = normalize_content_url(row[10]) if len(row) > 10 and row[10] else None
                iconimgpath = normalize_content_url(row[8]) if len(row) > 8 and row[8] else None
                
                # コンテンツタイプを推測
                content_type = infer_content_type(contentpath, row[9])
                
                result.append({
                    "title": row[0],
                    "contentpath": contentpath,
                    "thumbnailpath": thumbnailpath,
                    "type": content_type,
                    "spotlightnum": row[2],
                    "posttimestamp": row[3].isoformat(),
                    "playnum": row[4],
                    "link": row[5],
                    "username": row[6],
                    "user_id": row[7],
                    "iconimgpath": iconimgpath,
                    "spotlightflag": row[11],
                    "textflag": row[9],
                    "commentnum": row[12],
                    "contentID": row[13]
                })
        
        # 最後のcontentIDを更新（ループ判定用）
        if result:
            last_content_id = result[-1]["contentID"]
            update_last_contetid(uid, last_content_id)
            
            # ループ判定：取得可能なコンテンツ数と比較
            from models.content_get import get_content_id_range
            min_id, max_id, total_count = get_content_id_range(uid)
            # 取得件数が少ない場合、または取得したIDが範囲外の場合はループした可能性
            is_looped = (total_count > 0 and len(result) < 3) or \
                       (min_id is not None and last_content_id < min_id) or \
                       (max_id is not None and last_content_id > max_id)
        
        # 投稿一覧取得ログ（デバウンス確認用：実際に処理されたリクエストのみログ出力）
        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"投稿一覧取得:{username}")
        
        return jsonify({
            "status": "success",
            "message": f"{len(result)}件のコンテンツを取得",
            "data": result,
            "isLooped": is_looped if result else False
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# @content_bp.route('/getcontent', methods=['POST'])
# @jwt_required
# def get_content_designation():
#     try:
#         uid = request.user["firebase_uid"]
#         data = request.get_json()
#         contentID = data.get("contentID")
#         if not contentID:
#             return jsonify({"status": "success", "message": "contentIDが指定されていません", "data": []}), 200
#         rows = get_one_content(uid, contentID) #指定したコンテンツIDの詳細のみを取得
#         lastcontentid = None
#         # Dartで扱いやすいように整形
#         result = []
#         for row in rows:
#             # DBから取得したパスをCloudFront URLに正規化
#             contentpath = normalize_content_url(row[1]) if row[1] else None
#             thumbnailpath = normalize_content_url(row[10]) if len(row) > 10 and row[10] else None
#             iconimgpath = normalize_content_url(row[8]) if len(row) > 8 and row[8] else None
#             result.append({
#                 "title": row[0],
#                 "contentpath": contentpath,
#                 "thumbnailpath": thumbnailpath,
#                 "spotlightnum": row[2],
#                 "posttimestamp": row[3].isoformat(),
#                 "playnum": row[4],
#                 "link": row[5],
#                 "username": row[6],
#                 "user_id": row[7],  # userIDを追加
#                 "iconimgpath": iconimgpath,
#                 "spotlightflag": row[11],
#                 "textflag":row[9],
#                 "commentnum":row[12],
#                 "contentID":row[13]
#             })
#             lastcontentid = row[13]
#         update_last_contetid(uid, lastcontentid)

#         return jsonify({
#             "status": "success",
#             "message": f"{len(result)}件のコンテンツを取得",#"1件のコンテンツを取得"となる
#             "data": result
#         }), 200
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 400
        