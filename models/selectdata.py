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



def get_user_by_content_id(contentID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                'SELECT u.userID, u.username, u.iconimgpath, u.token, u.notificationenabled, c.title FROM content c JOIN "user" u ON c.userID = u.userID WHERE c.contentID = %s',
                (contentID,)
            )
            row = cur.fetchone()
        if row:
            return {
                "userID": row[0],
                "username": row[1],
                "iconimgpath": row[2],
                "token": row[3],
                "notificationenabled": row[4],
                "title": row[5],
            }
        return None
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None
    finally:
        if conn:
            release_connection(conn)

def get_user_by_parentcomment_id(contentID,parentcommentID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                'SELECT u.userID, u.username, u.iconimgpath, u.token, u.notificationenabled FROM coment c JOIN "user" u ON c.userID = u.userID WHERE c.contentID = %s contentID = %s',
                (contentID,parentcommentID)
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

def get_user_spotlightnum(userID):
    """ユーザごとのスポットライト数を取得"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT SUM(spotlightnum) FROM content where userID = %s', (userID,))
            row = cur.fetchone()
        if row:
            print(row[0])
            return row[0]
        return None, None
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None, None
    finally:
        if conn:
            release_connection(conn)

#実装済み
def get_play_content_id(contentID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            if contentID:
                # ① 指定された contentID の投稿時間を取得
                cur.execute(
                    "SELECT posttimestamp FROM content WHERE contentID = %s",
                    (contentID,)
                )
                row = cur.fetchone()
                if not row:
                    return None
                
                post_time = row[0]

                # ② その時間より後に投稿された最初のコンテンツを取得
                cur.execute(
                    """
                    SELECT contentID 
                    FROM content
                    WHERE posttimestamp < %s
                    ORDER BY posttimestamp DESC
                    LIMIT 1
                    """,
                    (post_time,)
                )
                next_row = cur.fetchone()
            else:
                # contentID が無い場合 → 最新投稿の contentID を取得
                cur.execute(
                    """
                    SELECT contentID
                    FROM content
                    ORDER BY posttimestamp DESC
                    LIMIT 1
                    """
                )
                next_row = cur.fetchone()
        if next_row:
            return next_row[0]
        return None
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None
    finally:
        if conn:
            release_connection(conn)


#------------------------------ここから要テスト------------------------------

def get_content_id():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT contentID FROM content")
            rows = cur.fetchall()
        return [r[0] for r in rows]
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None
    finally:
        if conn:
            release_connection(conn)

#実装済み
# 1️⃣ 指定されたコンテンツIDの情報を取得
def get_content_detail(contentID):
    """指定コンテンツの詳細を取得し、再生数を+1"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            
            # 詳細情報を取得
            cur.execute("""
                SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                       c.playnum, c.link, u.username, u.iconimgpath, c.textflag, c.thumbnailpath
                FROM content c
                JOIN "user" u ON c.userID = u.userID
                WHERE c.contentID = %s;
            """, (contentID,))
            row = cur.fetchone()
        conn.commit()
        return row
    except psycopg2.Error as e:
        print("❌ データベースエラー:", e)
        return None
    finally:
        if conn:
            release_connection(conn)


#実装済み
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

#実装済み
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


#実装済み
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


#実装済み
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

#実装済み
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

#実装済み
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


#実装済み
# 📘 特定プレイリスト内のコンテンツ一覧取得
def get_playlist_contents(userID, playlistID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.contentID, c.title, c.spotlightnum, c.posttimestamp,
                       c.playnum, c.link, c.thumbnailpath
                FROM playlistdetail pd
                JOIN content c ON pd.contentID = c.contentID
                WHERE pd.userID = %s AND pd.playlistID = %s
                
            """, (userID, playlistID))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー(get_playlist_contents):", e)
        return []
    finally:
        if conn:
            release_connection(conn)


# 8️⃣ プレイリストタイトル＋先頭サムネイル＋コンテンツ数
def get_playlists_with_thumbnail(userID):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    p.playlistID,
                    p.title,
                    c.thumbnailpath,
                    COUNT(pd.contentID) AS content_count
                FROM playlist p
                LEFT JOIN playlistdetail pd 
                    ON p.userID = pd.userID AND p.playlistID = pd.playlistID
                LEFT JOIN content c 
                    ON pd.contentID = c.contentID
                WHERE p.userID = %s
                GROUP BY p.playlistID, p.title, c.thumbnailpath
                ORDER BY p.playlistID
            """, (userID,))
            
            rows = cur.fetchall()

        # Dart側で扱いやすいように辞書形式へ変換
        result = [
            {
                "playlistID": row[0],
                "title": row[1],
                "thumbnailpath": row[2],
                "content_count": row[3]
            }
            for row in rows
        ]

        return result

    except psycopg2.Error as e:
        print("データベースエラー(get_playlists_with_thumbnail):", e)
        return []
    finally:
        if conn:
            release_connection(conn)




#実装済み
# 検索一致コンテンツ一覧
def get_search_contents(word):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    c.contentID, 
                    c.title, 
                    c.spotlightnum, 
                    c.posttimestamp, 
                    c.playnum, 
                    c.link, 
                    c.thumbnailpath
                FROM contentuser cu
                JOIN content c ON cu.contentID = c.contentID
                WHERE c.title ILIKE %s
            """, (f"%{word}%",))  # ← 部分一致検索（大文字小文字区別なし）
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


#通知の取得
def get_notification(uid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    n.notificationID,
                    n.notificationtimestamp,
                    n.contentuserCID,
                    n.contentuserUID,
                    cuu.username AS spotlight_user_name,
                    cuc.title AS spotlight_title,
                    n.comCTID,
                    n.comCMID,
                    cmc.title AS comment_content_title,
                    cm.commenttext,
                    cm.parentcommentID,
                    cmu.username AS comment_user_name,
                    n.notificationtext,
                    n.notificationtitle,
                    n.isread,
                    cuc.thumbnailpath as spotlight_thumbnailpath,
                    cmc.thumbnailpath as comment_thumbnailpath,
                    cuu.iconimgpath as spotlight_iconimgpath,
                    cmu.iconimgpath as comment_iconimgpath
                FROM notification n 
                LEFT JOIN "user" cuu ON n.contentuserUID = cuu.userID
                LEFT JOIN content cuc ON n.contentuserCID = cuc.contentID
                LEFT JOIN content cmc ON n.comCTID = cmc.contentID
                LEFT JOIN comment cm 
                    ON n.comCTID = cm.contentID 
                    AND n.comCMID = cm.commentID
                LEFT JOIN "user" cmu ON cm.userID = cmu.userID
                WHERE n.userID = %s
                ORDER BY n.notificationtimestamp DESC;
            """, (uid,))
            rows = cur.fetchall()
            cur.execute("""
                UPDATE notification
                SET isread = TRUE
                WHERE userID = %s
            """, (uid))
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)

#未読通知数の取得
def get_unloaded_num(uid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    count(*)
                FROM notification
                WHERE userID = %s AND isread = FALSE
            """, (uid,))
            row = cur.fetchone()
        return row[0] if row else 0
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return 0
    finally:
        if conn:
            release_connection(conn)
# print("-----------------------------全てのコンテンツID------------------------------------")
# print(get_content_id())
# print("-----------------------------指定したコンテンツの詳細------------------------------------")
# print(get_content_detail(1))
# print("-----------------------------指定したコンテンツのコメント------------------------------------")
# print(get_comments_by_content(1))
# print("-----------------------------指定したユーザの検索履歴------------------------------------")
# print(get_search_history("xonEecR0o2OcyDU9JJQXGBT3pYg2"))
# print("-----------------------------指定したユーザの検索履歴------------------------------------")
# print(get_search_history("testUser1"))
# print("-----------------------------指定したユーザの投稿コンテンツ------------------------------------")
# print(get_user_contents("xonEecR0o2OcyDU9JJQXGBT3pYg2"))
# print("-----------------------------指定したユーザの投稿コンテンツ------------------------------------")
# print(get_user_contents("testUser1"))
# print("-----------------------------指定したユーザがスポットライトを当てたコンテンツ------------------------------------")
# print(get_spotlight_contents("testUser1"))
# print("-----------------------------指定したユーザの再生履歴------------------------------------")
# print(get_play_history("testUser1"))
# print("-----------------------------指定したユーザのプレイリスト------------------------------------")
# print(get_playlists_with_thumbnail("xonEecR0o2OcyDU9JJQXGBT3pYg2"))
# print("-----------------------------指定したコンテンツのコメント[0]------------------------------------")
# print(get_comments_by_content(1)[0])
# print("-----------------------------指定したコンテンツのコメント[1]------------------------------------")
# print(get_comments_by_content(1)[1])
