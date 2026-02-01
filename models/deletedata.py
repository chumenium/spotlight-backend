import psycopg2
import os
from models.connection_pool import get_connection, release_connection
from utils.s3 import delete_file_from_url

# ============================================
# 1. 視聴履歴（playhistory）から特定の履歴を削除
# ============================================
def delete_play_history(userID, playID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # playIDに紐づくcontentIDを取得
            cur.execute("""
                SELECT contentID
                  FROM playhistory
                 WHERE userID = %s AND playID = %s
                 LIMIT 1
            """, (userID, playID))
            row = cur.fetchone()

            # 対象のplayIDを含め、同一contentIDの履歴をまとめて削除
            if row:
                content_id = row[0]
                cur.execute("""
                    DELETE FROM playhistory
                     WHERE userID = %s
                       AND contentID = %s
                """, (userID, content_id))
        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


# ============================================
# 2. プレイリストの中身の特定コンテンツを削除
# ============================================
def delete_playlist_detail(uid, playlistID, contentID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM playlistdetail
                WHERE userID = %s AND playlistID = %s AND contentID = %s
            """, (uid, playlistID, contentID))
        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


# ============================================
# 3. 特定のプレイリストを削除
#    → 連動して playlistdetail の中身も削除
# ============================================
def delete_playlist(uid, playlistID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:

            # まず中の詳細を削除
            cur.execute("""
                DELETE FROM playlistdetail
                WHERE userID = %s AND playlistID = %s
            """, (uid, playlistID))

            # プレイリスト本体を削除
            cur.execute("""
                DELETE FROM playlist
                WHERE userID = %s AND playlistID = %s
            """, (uid, playlistID))

        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


# ============================================
# 4. 検索履歴を削除（serchhistory）
# serchID（数値）の場合はその1行を削除、文字列の場合は従来通り serchword で削除（後方互換）
# ============================================
def delete_serch_history(uid, serchID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            try:
                sid = int(serchID)
                cur.execute("""
                    DELETE FROM serchhistory
                    WHERE userID = %s AND serchID = %s
                """, (uid, sid))
            except (TypeError, ValueError):
                cur.execute("""
                    DELETE FROM serchhistory
                    WHERE userID = %s AND serchword = %s
                """, (uid, serchID))
        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


# ============================================
# 5. 通知（notification）から特定の通知を削除
# ============================================
def delete_notification(uid, notificationID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM notification
                WHERE userID = %s AND notificationID = %s
            """, (uid, notificationID))
        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


# ============================================
# 6. コメント削除（contentID + commentID ペア）
# ============================================
def delete_comment(contentID, commentID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:

            #repotsに紐づくデータ削除
            cur.execute("""
                DELETE FROM reports
                WHERE comctid = %s OR comcmid = %s
            """, (contentID, commentID))

            # まず、このコメントに対する子コメント（parentcommentID）を削除
            cur.execute("""
                DELETE FROM comment
                WHERE contentID = %s AND parentcommentID = %s
            """, (contentID, commentID))

            # その後、コメント本体の削除
            cur.execute("""
                DELETE FROM comment
                WHERE contentID = %s AND commentID = %s
            """, (contentID, commentID))

        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


# ============================================
# 7. 特定のコンテンツを削除
#    → 関連テーブル（comment / playhistory / playlistdetail / notification / contentuser）も削除
#    → S3からもファイルを削除
# ============================================
def delete_content(uid, contentID):
    conn = None
    contentpath = None
    thumbnailpath = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # 削除前にコンテンツのURLを取得
            cur.execute("""
                SELECT contentpath, thumbnailpath
                FROM content
                WHERE userID = %s AND contentID = %s
            """, (uid, contentID))
            row = cur.fetchone()
            if row:
                contentpath = row[0]
                thumbnailpath = row[1]

            #repotsに紐づくデータ削除
            cur.execute("""
                DELETE FROM reports
                WHERE contentID = %s
            """, (contentID,))
            
            # ① notification に紐づくデータ削除
            cur.execute("""
                DELETE FROM notification
                WHERE contentuserCID = %s OR comCTID = %s
            """, (contentID, contentID))

            # ② コメント削除（親子全て）
            cur.execute("""
                DELETE FROM comment
                WHERE contentID = %s
            """, (contentID,))

            # ③ contentuser から削除
            cur.execute("""
                DELETE FROM contentuser
                WHERE contentID = %s
            """, (contentID,))

            # ④ playlistdetail から削除
            cur.execute("""
                DELETE FROM playlistdetail
                WHERE contentID = %s
            """, (contentID,))

            # ⑤ playhistory から削除
            cur.execute("""
                DELETE FROM playhistory
                WHERE contentID = %s
            """, (contentID,))

            # ⑥ 最後に content 本体を削除
            cur.execute("""
                DELETE FROM content
                WHERE userID = %s AND contentID = %s
            """, (uid, contentID))

        conn.commit()

        # S3からファイルを削除
        if contentpath and (contentpath.startswith('http://') or contentpath.startswith('https://')):
            try:
                delete_file_from_url(contentpath)
            except Exception as e:
                pass

        if thumbnailpath and (thumbnailpath.startswith('http://') or thumbnailpath.startswith('https://')):
            try:
                delete_file_from_url(thumbnailpath)
            except Exception as e:
                pass

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


def delete_content_by_admin(contentID):
    conn = None
    contentpath = None
    thumbnailpath = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # 削除前にコンテンツのURLを取得
            cur.execute("""
                SELECT contentpath, thumbnailpath
                FROM content
                WHERE contentID = %s
            """, (contentID,))
            row = cur.fetchone()
            if row:
                contentpath = row[0]
                thumbnailpath = row[1]

            #repotsに紐づくデータ削除
            cur.execute("""
                DELETE FROM reports
                WHERE contentID = %s
            """, (contentID,))
            
            # ① notification に紐づくデータ削除
            cur.execute("""
                DELETE FROM notification
                WHERE contentuserCID = %s OR comCTID = %s
            """, (contentID, contentID))

            # ② コメント削除（親子全て）
            cur.execute("""
                DELETE FROM comment
                WHERE contentID = %s
            """, (contentID,))

            # ③ contentuser から削除
            cur.execute("""
                DELETE FROM contentuser
                WHERE contentID = %s
            """, (contentID,))

            # ④ playlistdetail から削除
            cur.execute("""
                DELETE FROM playlistdetail
                WHERE contentID = %s
            """, (contentID,))

            # ⑤ playhistory から削除
            cur.execute("""
                DELETE FROM playhistory
                WHERE contentID = %s
            """, (contentID,))

            # ⑥ 最後に content 本体を削除
            cur.execute("""
                DELETE FROM content
                WHERE contentID = %s
            """, (contentID,))

        conn.commit()

        # S3からファイルを削除
        if contentpath and (contentpath.startswith('http://') or contentpath.startswith('https://')):
            try:
                delete_file_from_url(contentpath)
            except Exception as e:
                pass

        if thumbnailpath and (thumbnailpath.startswith('http://') or thumbnailpath.startswith('https://')):
            try:
                delete_file_from_url(thumbnailpath)
            except Exception as e:
                pass

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)

def delete_notification_contentuser(contentuserCID,contentuserUID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM notification
                WHERE contentuserCID = %s AND contentuserUID = %s
            """, (contentuserCID, contentuserUID))

        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


# ============================================
# ユーザーアカウント削除
#    → ユーザーの全コンテンツ、アイコンをS3から削除
#    → DBから全関連データを削除
# ============================================
def delete_user_account(userID):
    conn = None
    contents_to_delete = []
    iconpath = None
    
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # 削除前にユーザーのコンテンツ一覧とアイコンパスを取得
            # ① ユーザーの全コンテンツを取得（S3削除用）
            cur.execute("""
                SELECT contentID, contentpath, thumbnailpath
                FROM content
                WHERE userID = %s
            """, (userID,))
            contents_to_delete = cur.fetchall()
            
            # ② ユーザーのアイコンパスを取得（S3削除用）
            cur.execute("""
                SELECT iconimgpath
                FROM "user"
                WHERE userID = %s
            """, (userID,))
            icon_row = cur.fetchone()
            if icon_row:
                iconpath = icon_row[0]
            
            # ===== DB削除処理（外部キー制約の順序を考慮） =====
            
            # 1. reports（そのユーザーが報告した/されたもの）
            cur.execute("""
                DELETE FROM reports
                WHERE reportuidID = %s OR targetuidID = %s
            """, (userID, userID))
            
            # 2. notification（そのユーザーに関連する通知）
            cur.execute("""
                DELETE FROM notification
                WHERE userID = %s 
                   OR contentuserUID = %s 
                   OR contentuserCID IN (
                       SELECT contentID FROM content WHERE userID = %s
                   )
                   OR comCTID IN (
                       SELECT contentID FROM content WHERE userID = %s
                   )
            """, (userID, userID, userID, userID))
            
            # 3. comment（そのユーザーのコメント）
            cur.execute("""
                DELETE FROM comment
                WHERE userID = %s
            """, (userID,))
            
            # 4. contentuser（そのユーザーに関連するもの）
            cur.execute("""
                DELETE FROM contentuser
                WHERE userID = %s OR contentID IN (
                    SELECT contentID FROM content WHERE userID = %s
                )
            """, (userID, userID))
            
            # 5. playlistdetail（そのユーザーのプレイリスト詳細）
            cur.execute("""
                DELETE FROM playlistdetail
                WHERE userID = %s
            """, (userID,))
            
            # 6. playlist（そのユーザーのプレイリスト）
            cur.execute("""
                DELETE FROM playlist
                WHERE userID = %s
            """, (userID,))
            
            # 7. playhistory（そのユーザーの再生履歴）
            cur.execute("""
                DELETE FROM playhistory
                WHERE userID = %s
            """, (userID,))
            
            # 8. serchhistory（そのユーザーの検索履歴）
            cur.execute("""
                DELETE FROM serchhistory
                WHERE userID = %s
            """, (userID,))
            
            # 9. content（そのユーザーのコンテンツ）
            # 注: この時点でcontentuser, comment, notificationなどは既に削除済み
            cur.execute("""
                DELETE FROM content
                WHERE userID = %s
            """, (userID,))
            
            # 10. user（ユーザー本体）
            cur.execute("""
                DELETE FROM "user"
                WHERE userID = %s
            """, (userID,))
            
        conn.commit()
        
        # ===== S3からファイルを削除 =====
        # ① コンテンツファイルを削除
        for content_row in contents_to_delete:
            contentpath = content_row[1] if len(content_row) > 1 else None
            thumbnailpath = content_row[2] if len(content_row) > 2 else None
            
            # contentpathを削除
            if contentpath and (contentpath.startswith('http://') or contentpath.startswith('https://')):
                try:
                    delete_file_from_url(contentpath)
                except Exception as e:
                    pass
            
            # thumbnailpathを削除
            if thumbnailpath and (thumbnailpath.startswith('http://') or thumbnailpath.startswith('https://')):
                try:
                    delete_file_from_url(thumbnailpath)
                except Exception as e:
                    pass
        
        # ② アイコンファイルを削除（default_icon.pngは削除しない）
        if iconpath:
            from utils.s3 import extract_s3_key_from_url
            icon_key = extract_s3_key_from_url(iconpath)
            
            is_default_icon = False
            if icon_key:
                filename = icon_key.split("/")[-1] if "/" in icon_key else icon_key
                is_default_icon = filename == "default_icon.png" or icon_key == "icon/default_icon.png"
            
            if not is_default_icon and (iconpath.startswith('http://') or iconpath.startswith('https://')):
                try:
                    delete_file_from_url(iconpath)
                except Exception as e:
                    pass
        
        return True
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            release_connection(conn)