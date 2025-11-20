import psycopg2
from models.connection_pool import get_connection, release_connection


#実装済み
#----------------コンテンツを追加----------------
def add_content_and_link_to_users(contentpath, link, title, userID, thumbnailpath=None, textflag=None):
    """コンテンツを追加し、全ユーザと紐付け"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # コンテンツ追加
        cur.execute("""
            INSERT INTO content (contentpath, thumbnailpath, link, title, userID,textflag)
            VALUES (%s, %s, %s, %s, %s,%s)
            RETURNING contentID;
        """, (contentpath, thumbnailpath, link, title, userID,textflag))
        content_id = cur.fetchone()[0]

        # 全ユーザと紐付け（CROSS JOINで一括登録）
        cur.execute("""
            INSERT INTO contentuser (contentID, userID)
            SELECT %s AS contentID, u.userID
            FROM "user" AS u;
        """, (content_id,))

        conn.commit()
        print(f"コンテンツID {content_id} を全ユーザに紐付けました。")

    except psycopg2.Error as e:
        print("データベースエラー:", e)
        conn.rollback()
    finally:
        release_connection(conn)


#実装済み
#----------------コメントを追加----------------
def insert_comment(contentID, userID, commenttext, parentcommentID=None):
    """コメントを追加"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO comment (contentID, userID, commenttext, parentcommentID)
            VALUES (%s, %s, %s, %s)
            RETURNING commentID;
        """, (contentID, userID, commenttext, parentcommentID))
        comment_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ commentID={comment_id} を追加しました。")
        return comment_id
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None
    finally:
        if conn:
            release_connection(conn)

#実装済み
#----------------プレイリストを追加----------------
def insert_playlist(userID, title):
    """プレイリストを追加"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO playlist (userID, title)
            VALUES (%s, %s)
            RETURNING playlistID;
        """, (userID, title))
        playlist_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ playlistID={playlist_id} を追加しました。")
        return playlist_id
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None
    finally:
        if conn:
            release_connection(conn)

#実装済み
#----------------プレイリスト詳細を追加----------------
def insert_playlist_detail(userID, playlistID, contentID):
    """プレイリスト詳細を追加"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO playlistdetail (userID, playlistID, contentID)
            VALUES (%s, %s, %s);
        """, (userID, playlistID, contentID))
        conn.commit()
        print(f"✅ プレイリスト詳細を追加しました。")
    except psycopg2.Error as e:
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)


#実装済み
#----------------検索履歴を追加----------------
def insert_search_history(userID, serchword):
    """検索履歴を追加"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO serchhistory (userID, serchword)
            VALUES (%s, %s);
        """, (userID, serchword))
        conn.commit()
        print(f"✅ 検索履歴を追加しました。")
    except psycopg2.Error as e:
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)


#実装済み
#----------------再生履歴を追加----------------
def insert_play_history(userID, contentID):
    """再生履歴を追加"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO playhistory (userID, contentID)
            VALUES (%s, %s);
        """, (userID, contentID))
        conn.commit()
        print(f"✅ 再生履歴を追加しました。")
    except psycopg2.Error as e:
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)


#----------------通知履歴を追加----------------
def insert_notification(userID, contentuserCID=None, contentuserUID=None, comCTID=None, comCMID=None, notificationtext=None, notificationtitle=None):
    """通知履歴を追加"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO notification (userID, contentuserCID, contentuserUID, comCTID, comCMID, notificationtext, notificationtitle)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (userID, contentuserCID, contentuserUID, comCTID, comCMID, notificationtext, notificationtitle))
        conn.commit()
        print(f"✅ 通知履歴を追加しました。")
    except psycopg2.Error as e:
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)


