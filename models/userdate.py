import psycopg2
import os
from models.connection_pool import get_connection, release_connection
def update_FMCtoken(new_token, uid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('UPDATE "user" SET token = %s WHERE userID = %s', (new_token, uid))
        conn.commit()
        print("✅ tokenをアップデートしました。")
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)


def get_user_by_id(userID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                'SELECT userID, username, iconimgpath, token, notificationenabled FROM "user" WHERE userID = %s',
                (userID,)
            )
            row = cur.fetchone()
        if row:
            return {
                "userID": row[0],
                "username": row[1],
                "iconimgpath": row[2],
                "token": row[3],
                "notificationenabled": row[4],
            }
        return None
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None
    finally:
        if conn:
            release_connection(conn)

def user_exists(userID):
    """ユーザーが存在するか確認"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM "user" WHERE userID = %s', (userID,))
            count = cur.fetchone()[0]
        return count > 0
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return False
    finally:
        if conn:
            release_connection(conn)


def get_user_name_iconpath(userID):
    """ユーザ名とアイコン画像パスを取得"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT username, iconimgpath FROM "user" WHERE userID = %s', (userID,))
            row = cur.fetchone()
        if row:
            return row[0], row[1]
        return None, None
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None, None
    finally:
        if conn:
            release_connection(conn)




#------------------------------ここから要テスト------------------------------

# 1️⃣ 指定されたコンテンツIDの情報を取得
def get_content_detail(contentID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                       c.playnum, c.link, u.username, u.iconimgpath
                FROM content c
                JOIN "user" u ON c.userID = u.userID
                WHERE c.contentID = %s
            """, (contentID,))
            row = cur.fetchone()
        return row
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None
    finally:
        if conn:
            release_connection(conn)


# 2️⃣ 指定ユーザIDのコンテンツユーザからスポットライトフラグを取得
def get_user_spotlight_flag(userID, contentID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT spotlightflag 
                FROM contentuser 
                WHERE userID = %s AND contentID = %s
            """, (userID, contentID))
            row = cur.fetchone()
        return row[0] if row else False
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return False
    finally:
        if conn:
            release_connection(conn)


# 3️⃣ コメント情報を取得
def get_comments_by_content(contentID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.commentID, u.username, u.iconimgpath, 
                       c.commenttimestamp, c.commenttext, c.parentcommentID
                FROM comment c
                JOIN "user" u ON c.userID = u.userID
                WHERE c.contentID = %s
                ORDER BY c.commenttimestamp ASC
            """, (contentID,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


# 4️⃣ 検索履歴一覧を取得
def get_search_history(userID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT serchword 
                FROM serchhistory 
                WHERE userID = %s
                ORDER BY serchID DESC
            """, (userID,))
            rows = cur.fetchall()
        return [r[0] for r in rows]
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


# 5️⃣ 指定ユーザーが投稿したコンテンツ一覧
def get_user_contents(userID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT contentID, title, spotlightnum, posttimestamp, 
                       playnum, link, thumbnailpath
                FROM content
                WHERE userID = %s
                ORDER BY posttimestamp DESC
            """, (userID,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


# 6️⃣ スポットライト済みコンテンツ一覧
def get_spotlight_contents(userID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.contentID, c.title, c.spotlightnum, c.posttimestamp, 
                       c.playnum, c.link, c.thumbnailpath
                FROM contentuser cu
                JOIN content c ON cu.contentID = c.contentID
                WHERE cu.userID = %s AND cu.spotlightflag = TRUE
                ORDER BY c.posttimestamp DESC
            """, (userID,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


# 7️⃣ 再生履歴コンテンツ一覧
def get_play_history(userID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.contentID, c.title, c.spotlightnum, c.posttimestamp,
                       c.playnum, c.link, c.thumbnailpath
                FROM playhistory p
                JOIN content c ON p.contentID = c.contentID
                WHERE p.userID = %s
                ORDER BY p.playID DESC
            """, (userID,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


# 8️⃣ プレイリストタイトル＋先頭サムネイル
def get_playlists_with_thumbnail(userID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.title, c.thumbnailpath
                FROM playlist p
                LEFT JOIN playlistdetail pd 
                    ON p.userID = pd.userID AND p.playlistID = pd.playlistID
                LEFT JOIN content c ON pd.contentID = c.contentID
                WHERE p.userID = %s
                GROUP BY p.title, c.thumbnailpath, p.playlistID
                HAVING MIN(pd.contentID) IS NOT NULL
                ORDER BY p.playlistID
            """, (userID,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)

#get_user_name_iconpath("xonEecR0o2OcyDU9JJQXGBT3pYg2")