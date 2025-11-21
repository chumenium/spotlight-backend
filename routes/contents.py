"""
コンテンツ管理API
"""
from flask import Blueprint, request, jsonify
from utils.auth import jwt_required
from models.updatedata import spotlight_on, spotlight_off,add_playnum
from models.selectdata import (
    get_content_detail,get_user_spotlight_flag,get_comments_by_content,get_play_content_id,
    get_search_contents, get_playlists_with_thumbnail, get_playlist_contents, get_user_name_iconpath,
    get_user_by_content_id, get_user_by_id, get_user_by_parentcomment_id
)
from models.createdata import (
    add_content_and_link_to_users, insert_comment, insert_playlist, insert_playlist_detail,
    insert_search_history, insert_play_history, insert_notification
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
        username, iconimgpath = get_user_name_iconpath(uid)

        # --- 受信データ ---
        content_type = data.get("type")      # "video" | "image" | "audio" | "text"
        title = data.get("title")
        link = data.get("link")

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

            # --- S3にアップロード ---
            content_folder = subdirs[content_type]
            content_mime = get_content_type_from_extension(content_type, ext)
            
            # コンテンツ本体をS3にアップロード
            content_key = upload_to_s3(
                file_data=content_binary,
                folder=content_folder,
                filename=content_filename,
                content_type=content_mime
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
        contentID = data.get("contentID")
        user_data = get_user_by_id(uid)
        post_username = user_data["username"]
        if parentcommentid:
            commenid = insert_comment(
                contentID=contentID,
                userID=uid,
                commenttext=data.get("commenttext"),
                parentcommentID=parentcommentid
            )
            #投稿もとのコメント主に通知を送信
            posted_by_user_data = get_user_by_parentcomment_id(contentID, parentcommentid)
            if posted_by_user_data["notificationenabled"]:
                send_push_notification(posted_by_user_data["token"], "コメントが投稿されました","あなたが投稿したコメントに"+post_username+"さんがコメントを投稿しました")
                print(f"{posted_by_user_data['username']}に通知を送信")
            insert_notification(userID=posted_by_user_data["userID"],comCTID=contentID,comCMID=commentid)
        else:
            commentid = insert_comment(
                contentID=contentID,
                userID=uid,
                commenttext=data.get("commenttext"),
            )
            #投稿元のユーザに通知を送信
            content_user_data = get_user_by_content_id(contentID)
            if content_user_data["notificationenabled"]:
                title = content_user_data["title"]
                send_push_notification(content_user_data["token"], "コメントが投稿されました",title+"に"+post_username+"さんがコメントを投稿しました")
                print(f"{content_user_data['username']}に通知を送信")
            insert_notification(userID=content_user_data,comCTID=contentID,comCMID=commentid)

        return jsonify({"status": "success", "message": "コメントを追加しました。"}), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# 3️⃣ コンテンツ読み込み
# ===============================
@content_bp.route('/detail', methods=['POST'])
@jwt_required
def content_detail():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json() or {}
        contentID = data.get("contentID")
        
        # contentIDが指定されていない場合はランダムなコンテンツを取得
        if contentID is None:
            from models.selectdata import get_random_content_id
            nextcontentID = get_random_content_id()
        else:
            # 指定されたcontentIDを使用（後方互換性のため）
            nextcontentID = contentID
        
        if not nextcontentID:
            return jsonify({"status": "error", "message": "読み込み可能なコンテンツがありません"}), 200
        
        detail = get_content_detail(nextcontentID)
        # if not detail:
        #     return jsonify({"status": "error", "message": "コンテンツが見つかりません"}), 404

        spotlightflag = get_user_spotlight_flag(uid,nextcontentID)
        
        # DBから取得したパスをCloudFront URLに正規化（既存データの互換性のため）
        contentpath = normalize_content_url(detail[1])
        thumbnailpath = normalize_content_url(detail[9]) if len(detail) > 9 and detail[9] else None
        
        print("username:",detail[6])
        print("contentpath:",contentpath)
        print("thumbnailpath:",thumbnailpath)
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
                "iconimgpath": detail[7],
                "spotlightflag": spotlightflag,
                "textflag":detail[8],
                "nextcontentid": nextcontentID
            }
        }), 200
    except Exception as e:
        print("⚠️エラー:", e)
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
        add_playnum(contentID)
        insert_play_history(userID=uid,contentID=contentID)
        return jsonify({"status": "success", "message": "再生回数を追加"}), 200
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
        #投稿元のユーザに通知を送信
        content_user_data = get_user_by_content_id(contentID)
        spotlight_user = get_user_by_id(uid)  # if文の外で定義
        if content_user_data["notificationenabled"]:
            title = content_user_data["title"]
            send_push_notification(content_user_data["token"], "スポットライトが当てられました",title+"に"+spotlight_user["username"]+"さんがスポットライトを当てました")
            print(f"{content_user_data['username']}に通知を送信")
        insert_notification(userID=content_user_data["userID"],contentuserCID=contentID,contentuserUID=spotlight_user["userID"])
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
                "thumbnailpath": normalize_content_url(row[6]) if len(row) > 6 and row[6] else None,
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
            # DBから取得したパスをCloudFront URLに正規化
            thumbnailurl = normalize_content_url(row[6]) if len(row) > 6 and row[6] else None
            result.append({
                "contentID": row[0],
                "title": row[1],
                "spotlightnum": row[2],
                "posttimestamp": row[3],
                "playnum": row[4],
                "link": row[5],
                "thumbnailurl": thumbnailurl
            })

        return jsonify({
            "status": "success",
            "message": f"{len(result)}件のコンテンツが見つかりました。",
            "data": result
        }), 200
    except Exception as e:
        print("⚠️エラー:", e)
        return jsonify({"status": "error", "message": str(e)}), 400
        