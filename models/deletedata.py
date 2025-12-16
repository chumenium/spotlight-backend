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
            cur.execute("""
                DELETE FROM playhistory
                WHERE userID = %s AND playID = %s
            """, (userID, playID))
        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("データベースエラー:", e)
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
        print("データベースエラー:", e)
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
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)


# ============================================
# 4. 検索履歴を削除（serchhistory）
# ============================================
def delete_serch_history(uid, serchID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM serchhistory
                WHERE userID = %s AND serchword = %s
            """, (uid, serchID))
        conn.commit()

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("データベースエラー:", e)
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
        print("データベースエラー:", e)
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
        print("データベースエラー:", e)
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
                print(f"🗑️ S3からコンテンツファイルを削除: {contentpath}")
            except Exception as e:
                print(f"⚠️ S3削除エラー(contentpath): {e}")

        if thumbnailpath and (thumbnailpath.startswith('http://') or thumbnailpath.startswith('https://')):
            try:
                delete_file_from_url(thumbnailpath)
                print(f"🗑️ S3からサムネイルファイルを削除: {thumbnailpath}")
            except Exception as e:
                print(f"⚠️ S3削除エラー(thumbnailpath): {e}")

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("データベースエラー:", e)
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
                print(f"🗑️ S3からコンテンツファイルを削除: {contentpath}")
            except Exception as e:
                print(f"⚠️ S3削除エラー(contentpath): {e}")

        if thumbnailpath and (thumbnailpath.startswith('http://') or thumbnailpath.startswith('https://')):
            try:
                delete_file_from_url(thumbnailpath)
                print(f"🗑️ S3からサムネイルファイルを削除: {thumbnailpath}")
            except Exception as e:
                print(f"⚠️ S3削除エラー(thumbnailpath): {e}")

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("データベースエラー:", e)
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
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)