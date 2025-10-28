import psycopg2
from models.connection_pool import get_connection, release_connection

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
        print("✅ スポットライトをOFFにしました。")
    except psycopg2.Error as e:
        print("❌ データベースエラー:", e)
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)


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
