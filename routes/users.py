"""
ユーザー管理API
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from utils.auth import jwt_required
from models.selectdata import (
    get_user_name_iconpath,get_search_history,get_user_contents,get_spotlight_contents,
    get_play_history,get_user_spotlightnum,get_notification,get_unloaded_num,get_spotlight_num,
    get_spotlight_num_by_username, get_user_contents_by_username, get_bio_by_username, get_user_by_content_id,
    get_blocked_users, get_achievements_value
)
from models.deletedata import delete_user_account
from models.updatedata import enable_notification, disable_notification,chenge_icon, update_bio
from models.createdata import (
    add_content_and_link_to_users, insert_comment, insert_playlist, insert_playlist_detail,
    insert_search_history, insert_play_history, insert_notification, insert_report,
    insert_block, delete_block
)
from utils.s3 import upload_to_s3, get_cloudfront_url, delete_file_from_url, normalize_content_url
import os
import re
import base64

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

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


# ===============================
# 1️⃣ ユーザネームとアイコン画像のパスを取得
# ===============================
@users_bp.route('/getusername', methods=['POST'])
@jwt_required
def get_username():
    try:
        uid = request.user["firebase_uid"]
        username, iconimgpath, admin, bio = get_user_name_iconpath(uid)
        
        # DBから取得したパスをCloudFront URLに正規化（既存データの互換性のため）
        from utils.s3 import normalize_content_url
        normalized_iconpath = normalize_content_url(iconimgpath) if iconimgpath else None
        return jsonify({
            "status": "success",
            "data": {
                "firebase_uid": uid,
                "username": username,
                "iconimgpath": normalized_iconpath,
                "admin": admin,
                "bio": bio
            }
        }), 200
    except Exception as e:
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
        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"通知設定変更:{username}")
        return jsonify({"status": "success", "message": "通知をONにしました"}), 200
    except Exception as e:
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
        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"通知設定変更:{username}")
        return jsonify({"status": "success", "message": "通知をOFFにしました"}), 200
    except Exception as e:
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
        from utils.s3 import normalize_content_url
        contents = []
        for row in rows:
            content = {
                "contentID": row[0],
                "title": row[1],
                "spotlightnum": row[2],
                "posttimestamp": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None,
                "playnum": row[4],
                "link": row[5],
                "thumbnailpath": normalize_content_url(row[6]) if len(row) > 6 and row[6] else None,
                "username": str(row[7]) if row[7] is not None else None,
                "iconimgpath": normalize_content_url(row[8]) if len(row) > 8 and row[8] else None,
            }

            # contentpath（メディア本体のURL）も返す（audio/video再生用）
            if len(row) > 9 and row[9]:
                content["contentpath"] = normalize_content_url(row[9])

            contents.append(content)

        return jsonify({"status": "success", "data": contents}), 200

    except Exception as e:
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

        from utils.s3 import normalize_content_url
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
                "thumbnailpath": normalize_content_url(row[6]) if len(row) > 6 and row[6] else None,
                "username": str(row[7]) if row[7] is not None else None,
                "iconimgpath": normalize_content_url(row[8]) if len(row) > 8 and row[8] else None,
            }
            for row in rows
        ]

        # contentpath（メディア本体のURL）も返す（audio/video再生用）
        for i, row in enumerate(rows):
            if len(row) > 9 and row[9]:
                contents[i]["contentpath"] = normalize_content_url(row[9])

        return jsonify({"status": "success", "data": contents}), 200

    except Exception as e:
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
        return jsonify({"status": "error", "message": str(e)}), 400


# ===============================
# ブロック/ブロック解除
# ===============================
@users_bp.route('/block', methods=['POST'])
@jwt_required
def block_user():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        target_uid = data.get("target_uid")

        if not target_uid:
            return jsonify({"status": "error", "message": "target_uidが必要です"}), 400
        if target_uid == uid:
            return jsonify({"status": "error", "message": "自分自身はブロックできません"}), 400

        ok = insert_block(uid, target_uid)
        if not ok:
            return jsonify({"status": "error", "message": "ブロックに失敗しました"}), 400

        return jsonify({"status": "success", "message": "ブロックしました"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@users_bp.route('/unblock', methods=['POST'])
@jwt_required
def unblock_user():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        target_uid = data.get("target_uid")

        if not target_uid:
            return jsonify({"status": "error", "message": "target_uidが必要です"}), 400

        ok = delete_block(uid, target_uid)
        if not ok:
            return jsonify({"status": "error", "message": "ブロック解除に失敗しました"}), 400

        return jsonify({"status": "success", "message": "ブロックを解除しました"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@users_bp.route('/blockedusers', methods=['POST'])
@jwt_required
def get_blocked_users_api():
    try:
        uid = request.user["firebase_uid"]
        rows = get_blocked_users(uid)
        result = [
            {"userID": row[0], "username": row[1]}
            for row in rows
        ]
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


#自己紹介文を更新する処理
@users_bp.route('/updatebio', methods=['POST'])
@jwt_required
def update_bio_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        bio = data.get("bio", "").strip() if data.get("bio") else ""
        
        # 文字数チェック
        if len(bio) > 200:
            return jsonify({
                "status": "error",
                "message": "自己紹介文は200文字以内で入力してください"
            }), 400
        
        # データベースを更新
        update_bio(uid, bio if bio else None)
        username, _, _, _ = get_user_name_iconpath(uid)
        print(f"プロフィール更新:{username}")
        return jsonify({
            "status": "success",
            "message": "自己紹介文を更新しました"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "サーバーエラーが発生しました"
        }), 500

#アイコン変更の処理
@users_bp.route('/changeicon', methods=['POST'])
@jwt_required
def change_icon():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        username = data.get("username")
        file = data.get("iconimg")
        
        # 古いアイコンパスを取得
        username1, old_icon_url, admin, _ = get_user_name_iconpath(uid)
        
        # 古いアイコンをS3から削除（default_icon.pngは削除しない）
        if old_icon_url:
            # default_icon.pngかどうかをチェック
            # S3キーを抽出してファイル名を確認
            from utils.s3 import extract_s3_key_from_url
            old_icon_key = extract_s3_key_from_url(old_icon_url)
            
            # ファイル名がdefault_icon.pngかどうかをチェック
            # S3キーは "icon/default_icon.png" または "icon/xxx_icon.png" の形式
            is_default_icon = False
            if old_icon_key:
                # ファイル名を抽出（最後のスラッシュ以降）
                filename = old_icon_key.split("/")[-1] if "/" in old_icon_key else old_icon_key
                # default_icon.pngかどうかを厳密にチェック
                is_default_icon = filename == "default_icon.png" or old_icon_key == "icon/default_icon.png"
            
            if not is_default_icon:
                try:
                    delete_file_from_url(old_icon_url)
                except Exception as e:
                    # S3削除エラーは無視（ファイルが既に存在しない場合など）
                    pass
        
        # fileが空文字列、None、または空の場合はデフォルトアイコンに設定
        if file and file.strip() and file != "default_icon.jpg":
            if file.startswith("data:image"):
                file = file.split(",")[1]
            
            # Base64 → バイナリ変換
            icon_binary = base64.b64decode(file)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            # ファイル名生成（username_icon.png形式で、既存ファイルを上書き）
            filename = f"{username}_{timestamp}_icon.png"
            
            # ===== S3にアップロード（既存ファイルがある場合は上書き） =====
            upload_to_s3(
                file_data=icon_binary,
                folder="icon",
                filename=filename,
                content_type="image/png"
            )
            
            # ===== CloudFront URL生成 =====
            iconimgpath = get_cloudfront_url("icon", filename)
        else:
            # デフォルトアイコンの場合（fileが空、None、またはdefault_icon.jpgの場合）
            filename = "default_icon.png"
            iconimgpath = get_cloudfront_url("icon", filename)

        # ===== DBにCloudFront URLを保存 =====
        chenge_icon(uid, iconimgpath)
        print(f"アイコン変更:{username}")
        return jsonify({
            "status": "success",
            "message": "アイコンを変更しました。",
            "iconimgpath": iconimgpath
        }), 200

    except Exception as e:
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

            # アイコンパスとサムネイルパスをCloudFront URLに正規化
            from utils.s3 import normalize_content_url
            normalized_iconpath = normalize_content_url(iconpath) if iconpath else None
            normalized_thumbnailpath = normalize_content_url(thumbnailpath) if thumbnailpath else None
            
            notification_list.append({
                "notificationID": notificationID,
                "type": nt_type,
                "title": title,
                "text": text,
                "contenttitle":contenttitle,
                "iconpath":normalized_iconpath,
                "thumbnailpath":normalized_thumbnailpath,
                "contentID":contentID,
                "timestamp": timestamp_str,
                "isread":isread,
                
            })

        return jsonify({"status": "success", "data": notification_list}), 200

    except Exception as e:
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
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@users_bp.route('/report', methods=['POST'])
@jwt_required
def send_report_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        rtype = data.get("type")
        reason = data.get("reason")
        detail = data.get("detail")
        username, _, _, _ = get_user_name_iconpath(uid)
        if rtype == "user":
            targetuid = data.get("uid")
            insert_report(reporttype=rtype, reportuidID=uid, targetuidID=targetuid, reason=reason, detail=detail)
            target_username, _, _, _ = get_user_name_iconpath(targetuid)
            print(f"通報(ユーザー):{username}:対象({target_username})")
        elif rtype == "content":
            contentid1 = data.get("contentID")
            insert_report(reporttype=rtype, reportuidID=uid, contentID=contentid1, reason=reason, detail=detail)
            content_data = get_user_by_content_id(contentid1)
            content_title = content_data["title"]
            print(f"通報(投稿):{username}:\"{truncate_title(content_title)}\"")
        elif rtype == "comment":
            contentid2 = data.get("contentID")
            commentid = data.get("commentID")
            insert_report(reporttype=rtype, reportuidID=uid, comCTID=contentid2, comCMID=commentid, reason=reason, detail=detail)
            content_data = get_user_by_content_id(contentid2)
            content_title = content_data["title"]
            print(f"通報(投稿):{username}:\"{truncate_title(content_title)}\"")
        else:
            return jsonify({
                "status": "error",
                "message": str("inappropriate report type")
            }), 400
        return jsonify({
                "status": "success",
                "message": "通報を送信しました"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

#ユーザごとのスポットライト数を取得する
@users_bp.route('/getspotlightnum', methods=['POST'])
@jwt_required
def get_spotlight_num_api():
    try:
        uid = request.user["firebase_uid"]
        num = get_spotlight_num(uid)
        return jsonify({"status": "success", "num": num}), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


#ユーザプロフィールを取得する
@users_bp.route('/userhome', methods=['POST'])
@jwt_required
def get_user_home_api():
    try:
        uid = request.user["firebase_uid"]
        data = request.get_json()
        username = data.get("username")
        usericon = data.get("usericon")
        spotlightnum = get_spotlight_num_by_username(username)
        bio = get_bio_by_username(username)
        contentdata = get_user_contents_by_username(username)
        contents = []
        for row in contentdata:
            # DBから取得したパスをCloudFront URLに正規化
            thumbnailurl = normalize_content_url(row[6]) if len(row) > 6 and row[6] else None
            contentpath = normalize_content_url(row[7]) if len(row) > 7 and row[7] else None
            contents.append({
                "contentID": row[0],
                "title": row[1],
                "spotlightnum": row[2],
                "posttimestamp": row[3],
                "playnum": row[4],
                "link": row[5],
                "thumbnailurl": thumbnailurl,
                "contentpath": contentpath,
            })
        data = {
            "username":username,
            "usericon":usericon,
            "spotlightnum":spotlightnum,
            "bio": bio,
            "contents":contents
        }
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


# ===============================
# アカウント削除
# ===============================
@users_bp.route('/deleteaccount', methods=['POST'])
@jwt_required
def delete_account_api():
    try:
        uid = request.user["firebase_uid"]
        username, _, _, _ = get_user_name_iconpath(uid)
        
        # ユーザーアカウントと関連データを削除（DBとS3から）
        success = delete_user_account(uid)
        
        if success:
            print(f"アカウント削除:{username}")
            return jsonify({
                "status": "success",
                "message": "アカウントを削除しました"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "アカウントの削除に失敗しました"
            }), 500
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@users_bp.route('/getAchievements', methods=['POST'])
@jwt_required
def get_achievements_api():
    #自分が何回スポットライトしたか
    #自分が何回コメントを送信したか
    #自分が何回投稿したか
    #自分の投稿の視聴回数
    try:
        uid = request.user["firebase_uid"]
        spotlightnum, commentnum, contentnum, plyanum = get_achievements_value(uid)
        data = {
            "spotlightnum":spotlightnum,
            "commentnum":commentnum,
            "contentnum":contentnum,
            "plyanum": plyanum
        }
        print(spotlightnum,commentnum,contentnum,plyanum)
        return jsonify({"status": "success", "data": data}), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400