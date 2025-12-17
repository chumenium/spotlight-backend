import psycopg2
from models.connection_pool import get_connection, release_connection


#実装済み
#----------------コンテンツを追加----------------
def add_content_and_link_to_users(contentpath, link, title, userID, thumbnailpath=None, textflag=None, tag=None):
    """コンテンツを追加し、全ユーザと紐付け"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # コンテンツ追加
        cur.execute("""
            INSERT INTO content (contentpath, thumbnailpath, link, title, userID, textflag, tag)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING contentID;
        """, (contentpath, thumbnailpath, link, title, userID,textflag,tag))
        content_id = cur.fetchone()[0]

        # 全ユーザと紐付け（CROSS JOINで一括登録）
        cur.execute("""
            INSERT INTO contentuser (contentID, userID)
            SELECT %s AS contentID, u.userID
            FROM "user" AS u;
        """, (content_id,))

        conn.commit()

    except psycopg2.Error as e:
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
        return comment_id
    except psycopg2.Error as e:
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
        return playlist_id
    except psycopg2.Error as e:
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
    except psycopg2.Error as e:
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
    except psycopg2.Error as e:
    finally:
        if conn:
            release_connection(conn)


#実装済み
#----------------再生履歴を追加----------------
def insert_play_history(userID, contentID):
    """再生履歴を追加（重複チェック付き）"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        # 重複チェック：既に同じユーザー・コンテンツの再生履歴が存在するか確認
        cur.execute("""
            SELECT playID FROM playhistory 
            WHERE userID = %s AND contentID = %s 
            ORDER BY playID DESC LIMIT 1
        """, (userID, contentID))
        existing = cur.fetchone()
        
        # 重複がない場合のみ追加
        if not existing:
            cur.execute("""
                INSERT INTO playhistory (userID, contentID)
                VALUES (%s, %s);
            """, (userID, contentID))
            conn.commit()
        # デバッグ用のprint文を削除（コスト削減のため）
    except psycopg2.Error as e:
        # データベースエラーは無視（重複エラーなどは正常な動作）
        if conn:
            conn.rollback()
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
    except psycopg2.Error as e:
    finally:
        if conn:
            release_connection(conn)




# ---------------- 通報履歴を追加 ----------------
def insert_report(
    reporttype,
    reportuidID,
    targetuidID=None,
    contentID=None,
    comCTID=None,
    comCMID=None,
    reason=None,
    detail=None
):
    """reports テーブルに通報データを登録する"""

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reports (reporttype, reportuidID, targetuidID, contentID, comCTID, comCMID, reason, detail)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            reporttype,
            reportuidID,
            targetuidID,
            contentID,
            comCTID,
            comCMID,
            reason,
            detail
        ))
        conn.commit()

    except psycopg2.Error as e:

    finally:
        if conn:
            release_connection(conn)
