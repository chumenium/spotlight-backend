import psycopg2
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
        print("✅ スポットライトをONにしました。")
    except psycopg2.Error as e:
        print("❌ データベースエラー:", e)
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
        print("✅ スポットライトをOFFにしました。")
    except psycopg2.Error as e:
        print("❌ データベースエラー:", e)
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
        print("✅ 通知をONにしました。")
    except psycopg2.Error as e:
        print("❌ データベースエラー:", e)
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
        print("✅ 通知をOFFにしました。")
    except psycopg2.Error as e:
        print("❌ データベースエラー:", e)
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
        print(f"✅ アイコンを変更しました。")
    except psycopg2.Error as e:
        print("データベースエラー:", e)
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
        print(f"Add play count")
    except psycopg2.Error as e:
        print("データベースエラー:", e)
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
        print(f"✅ 自己紹介文を更新しました。")
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)