import psycopg2
from models.connection_pool import get_connection, release_connection


def update_FMCtoken(new_token, uid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('UPDATE "user" SET token = %s WHERE userID = %s', (new_token, uid))
        conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)

#実装済み
def spotlight_on(contentID, userID):
    """スポットライトON：カウント+1 & ユーザフラグTrue"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE content
                SET spotlightnum = spotlightnum + 1
                WHERE contentID = %s;
            """, (contentID,))
            cur.execute("""
                UPDATE contentuser
                SET spotlightflag = TRUE
                WHERE contentID = %s AND userID = %s;
            """, (contentID, userID))
        conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


from models.deletedata import delete_notification_contentuser
#実装済み
def spotlight_off(contentID, userID):
    """スポットライトOFF：カウント-1 & ユーザフラグFalse"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE content
                SET spotlightnum = GREATEST(spotlightnum - 1, 0)
                WHERE contentID = %s;
            """, (contentID,))
            cur.execute("""
                UPDATE contentuser
                SET spotlightflag = FALSE
                WHERE contentID = %s AND userID = %s;
            """, (contentID, userID))
        conn.commit()
        delete_notification_contentuser(contentID,userID)
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)

#実装済み
def enable_notification(userID):
    """通知ON"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "user"
                SET notificationenabled = TRUE
                WHERE userID = %s;
            """, (userID,))
        conn.commit()
    except psycopg2.Error as e:
        pass
    finally:
        if conn:
            release_connection(conn)


#実装済み
def disable_notification(userID):
    """通知OFF"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "user"
                SET notificationenabled = FALSE
                WHERE userID = %s;
            """, (userID,))
        conn.commit()
    except psycopg2.Error as e:
        pass
    finally:
        if conn:
            release_connection(conn)


#実装済み
#----------------アイコンを変更----------------
def chenge_icon(userID, iconimgpath):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "user" SET iconimgpath = %s WHERE userID = %s;
            """, (iconimgpath, userID))
        conn.commit()
    except psycopg2.Error as e:
        pass
    finally:
        if conn:
            release_connection(conn)


#----------------再生回数を追加----------------
def add_playnum(contentID):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # 再生回数を+1
            cur.execute("""
                UPDATE content
                SET playnum = playnum + 1
                WHERE contentID = %s;
            """, (contentID,))
        conn.commit()
        # デバッグ用のprint文を削除（コスト削減のため）
    except psycopg2.Error as e:
        # データベースエラーは無視（ログ削減のため）
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)

#----------------投稿のタイトル・タグを更新（自分の投稿のみ）----------------
def update_content_title_tag(contentID, userID, title=None, tag=None):
    """投稿の title / tag を更新。WHERE userID で自分の投稿のみ。"""
    if title is None and tag is None:
        return False
    conn = None
    try:
        conn = get_connection()
        sets = []
        params = []
        if title is not None:
            sets.append("title = %s")
            params.append(title)
        if tag is not None:
            sets.append("tag = %s")
            params.append(tag)
        params.extend([contentID, userID])
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE content SET " + ", ".join(sets) + " WHERE contentID = %s AND userID = %s",
                params
            )
            updated = cur.rowcount
        conn.commit()
        return updated > 0
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            release_connection(conn)


#----------------自己紹介文を更新----------------
def update_bio(userID, bio):
    """自己紹介文を更新"""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "user" SET bio = %s WHERE userID = %s;
            """, (bio if bio else None, userID))
        conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)