"""
管理者管理API
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from utils.auth import jwt_required
from models.admin_sql import (
    get_all_user_data, uid_admin_auth, disable_admin, enable_admin, get_reports_data,process_report,unprocess_report,get_content_data
)
from models.deletedata import (
    delete_content_by_admin,delete_comment
)
from utils.s3 import upload_to_s3, get_cloudfront_url, delete_file_from_url


admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ===============================
# 全ユーザの情報取得
# ===============================
@admin_bp.route('/getuser', methods=['POST'])
@jwt_required
def get_user_by_admin_api():
    try:
        userdatas = []
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            offset = data.get("offset")
            datas = get_all_user_data(offset)
            for row in datas:
                userdatas.append({
                    "userID": row[0],       #ユーザのID
                    "username": row[1],     #ユーザ名
                    "iconimgpath": row[2],  #ユーザアイコンのURL
                    "admin": row[3],        #管理者かどうか(False, True)
                    "spotlightnum": row[4], #そのユーザの合計スポットライト数
                    "reportnum": row[5],    #ユーザが通報した数
                    "reportednum": row[6]   #ユーザが関連するコンテンツ、コメントが通報された回数
                })
            return jsonify({
                "status": "success",
                "userdatas" :userdatas
            }), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


#当該ユーザを管理者にする
@admin_bp.route('/enableadmin', methods=['POST'])
@jwt_required
def enable_admin_api():
    try:
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            uid = data.get("userID")
            enable_admin(uid)
            return jsonify({"status": "success", "message": f"{uid}を管理者に変更"}), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


#当該ユーザを一般ユーザにする
@admin_bp.route('/disableadmin', methods=['POST'])
@jwt_required
def disable_admin_api():
    try:
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            uid = data.get("userID")
            disable_admin(uid)
            return jsonify({"status": "success", "message": f"{uid}を一般ユーザに変更"}), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400



#通報を取得
@admin_bp.route('/report', methods=['POST'])
@jwt_required
def get_report_api():
    try:
        reports = []
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            offset = data.get("offset")
            datas = get_reports_data(offset)
            for row in datas:
                reports.append({
                    "reportID": row[0],     #通報のID
                    "reporttype": row[1],   #通報の種類("user","contet","comment")
                    "reportuidID": row[2],  #通報したユーザのID
                    "username": row[3],     #通報したユーザの名前
                    "targetuidID": row[4],  #通報されたユーザのID
                    "targetusername": row[5],     #通報されたユーザの名前
                    "contentID": row[6],    #通報されたコンテンツのID
                    "comCTID": row[7],      #通報されたコメントのコンテンツID
                    "comCMID": row[8],      #通報されたコメントのコメントID   
                    "commenttext": row[9],  #コメントテキスト
                    "title": row[10],        #通報されたコンテンツのタイトル
                    "processflag": row[11] ,   #通報の処理状態(False, True)
                    "reason": row[12] ,       #通報の理由
                    "detail": row[13] or None,      #通報の詳細
                    "reporttimestamp": row[14]        #通報の時間
                })
            return jsonify({
                "status": "success",
                "reports" :reports
            }), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

#コンテンツを削除
@admin_bp.route('/deletecontent', methods=['POST'])
@jwt_required
def delete_content_by_admin_api():
    try:
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            contentid = data.get("contentID")
            delete_content_by_admin(contentid)
            return jsonify({"status": "success", "message": "該当コンテンツを削除"}), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

#コメントを削除
@admin_bp.route('/deletecomment', methods=['POST'])
@jwt_required
def delete_comment_by_admin_api():
    try:
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            contentid = data.get("contentID")
            commentid = data.get("commentID")
            delete_comment(contentid,commentid)
            return jsonify({"status": "success", "message": "該当コメントを削除"}), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


#通報を処理
@admin_bp.route('/processreport', methods=['POST'])
@jwt_required
def process_report_api():
    try:
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            reportid = data.get("reportID")
            process_report(reportid)
            return jsonify({"status": "success", "message": "通報を処理"}), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

#通報を処理解除
@admin_bp.route('/unprocessreport', methods=['POST'])
@jwt_required
def unprocess_report_api():
    try:
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            reportid = data.get("reportID")

            unprocess_report(reportid)
            return jsonify({"status": "success", "message": "通報を処理解除"}), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

#コンテンツ情報を取得
@admin_bp.route('/content2', methods=['POST'])
@jwt_required
def content_management():
    try:
        contents = []
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            offset = data.get("offset")
            datas = get_content_data(offset)
            for row in datas:
                contents.append({
                    "contentID": row[0],        #コンテンツのID
                    "spotlightnum": row[1],     #コンテンツのスポットライト数
                    "playnum": row[2],          #再生回数
                    "contentpath": row[3],      #コンテンツURL
                    "thumbnailpath": row[4],    #サムネイルURL
                    "title": row[5],            #タイトル
                    "tag": row[6],              #タグ
                    "posttimestamp": row[7],    #コンテンツの投稿時間
                    "userID": row[8],           #投稿したユーザのID
                    "username": row[9],         #ユーザネーム
                    "commentnum": row[10],       #コメント数
                    "reportnum": row[11]        #通報された件数
                })
            return jsonify({
                "status": "success",
                "contents" :contents
            }), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

#全てPOSTメソッド
# 最大取得件数はすべて共通して300件まで
# offsetに取得開始の値を入れる
# /api/admin/getuser "offset"に取得する件数を入れる0→300→600
# userdatas.append({
#     "userID": row[0],       #ユーザのID
#     "username": row[1],     #ユーザ名
#     "iconimgpath": row[2],  #ユーザアイコンのURL
#     "admin": row[3],        #管理者かどうか(False, True)
#     "spotlightnum": row[4], #そのユーザの合計スポットライト数
#     "reportnum": row[5],    #ユーザが通報した数
#     "reportednum": row[6]   #ユーザが関連するコンテンツ、コメントが通報された回数
# })            
# return jsonify({
#     "status": "success",
#     "userdatas" :userdatas
# }), 200

# /api/admin/enableadmin "userID"に管理者にしたいuserのuserIDを入れる
# return jsonify({"status": "success", "message": f"{uid}を管理者に変更"}), 200

# /api/admin/disableadmin "userID"に一般ユーザにしたいuserのuserIDを入れる
# return jsonify({"status": "success", "message": f"{uid}を一般ユーザに変更"}), 200

# /api/admin/content "offset"に取得する件数を入れる0→300→600
# for row in datas:
#     contents.append({
#         "contentID": row[0],        #コンテンツのID
#         "spotlightnum": row[1],     #コンテンツのスポットライト数
#         "playnum": row[2],          #再生回数
#         "contentpath": row[3],      #コンテンツURL
#         "thumbnailpath": row[4],    #サムネイルURL
#         "title": row[5],            #タイトル
#         "tag": row[6],              #タグ
#         "posttimestamp": row[7],    #コンテンツの投稿時間
#         "userID": row[8],           #投稿したユーザのID
#         "username": row[9],         #ユーザネーム
#         "commentnum": row[10],       #コメント数
#         "reportnum": row[11]        #通報された件数
#     })
# return jsonify({
#     "status": "success",
#     "contents" :contents
# }), 200

# /api/admin/deletecontent "contentID"に削除したいcontentのcontentIDを入れる
# return jsonify({"status": "success", "message": "該当コンテンツを削除"}), 200

# /api/admin/deletecomment "contentID"に削除したいコメントがあるコンテンツのcontentIDを"commentID"に削除したいコメントのcommentIDを入れる
# return jsonify({"status": "success", "message": "該当コメントを削除"}), 200



# @admin_bp.route('/xxxxx', methods=['POST'])
# @jwt_required
# def xxxxx():
#     try:
#         uid = request.user["firebase_uid"]
#         if uid_admin_auth(uid):


#             return jsonify({"status": "success", "message": "xxxxx"}), 200
#         else:
# #             return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
#     except Exception as e:
# #         return jsonify({"status": "error", "message": str(e)}), 400


from utils.notification import send_push_notification
from models.selectdata import get_user_by_id
from models.admin_sql import get_all_user_token
from models.createdata import insert_notification
#システムからの通知
@admin_bp.route('/adminnotification', methods=['POST'])
@jwt_required
def admin_send_notification():
    try:
        uid = request.user["firebase_uid"]
        if uid_admin_auth(uid):
            data = request.get_json()
            message = data.get("message")
            title = data.get("title")
            targetuid = data.get("targetuid")
            if targetuid == "all":
                users = get_all_user_token()
                tokens = []
                for user in users:
                    token = user.get("token")
                    enabled = user.get("notificationenabled", True)
                    if not token or not enabled:
                        continue
                    #同一端末に複数アカウントがある場合一度のみプッシュ通知を行う
                    if not(token in tokens):
                        send_push_notification(token, title, message)
                        tokens.append(token)
                        
                    insert_notification(
                        userID=user.get("userID"),
                        notificationtext=message,
                        notificationtitle=title
                    )
                return jsonify({
                    "status": "success",
                    "message": "通知を送信しました"
                }), 200
            else:
                user = get_user_by_id(targetuid)
                if not user or not user.get("token") or not user.get("notificationenabled", True):
                    return jsonify({"status": "error", "message": "通知送信対象が無効です"}), 400
                send_push_notification(user["token"], title, message)
                insert_notification(
                    userID=user["userID"],
                    notificationtext=message,
                    notificationtitle=title
                )
                return jsonify({
                    "status": "success",
                    "message": "通知を送信しました"
                }), 200
        else:
            return jsonify({"status": "error", "message": "管理者以外からのアクセス"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400