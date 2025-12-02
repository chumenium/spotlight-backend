import psycopg2
from models.connection_pool import get_connection, release_connection

def uid_admin_auth(uid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT admin FROM "user" WHERE userID = %s;
                """
            ,(uid,))
            row = cur.fetchone()
        return row[0] if row else 0
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


#ユーザ情報一覧を取得する
def get_all_user_data():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.userID, u.username,u.iconimgpath, u.admin, 
                COALESCE((SELECT SUM(spotlightnum) FROM content WHERE userID = u.userID) ,0)AS spotlightnum,
                COALESCE((SELECT COUNT(*) FROM reports WHERE reportuidid = u.userID) ,0)AS reportnum,
                COALESCE((SELECT 
                COUNT(*)
                FROM reports r
                LEFT OUTER JOIN content c ON r.contentid = c.contentID
                LEFT OUTER JOIN comment cm ON r.comctid = cm.contentID AND r.comcmid = cm.commentID
                WHERE r.targetuidid = 'pSpFtMWYhnPE8UrcdgiulXewqZt1' OR c.userID = u.userID OR cm.userID = u.userID
                ),0) AS reportednum
                FROM "user" u;
                """
            )
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)
