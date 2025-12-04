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
def get_all_user_data(offset):
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
                WHERE r.targetuidid = u.userID OR c.userID = u.userID OR cm.userID = u.userID
                ),0) AS reportednum
                FROM "user" u
                ORDER BY id ASC
                LIMIT 300 OFFSET %s;
                """
            ,(offset,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


#管理者に変更
def enable_admin(userID):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "user" SET admin = True WHERE userID = %s;
            """, (userID,))
        conn.commit()
        print(f"✅ アイコンを変更しました。")
    except psycopg2.Error as e:
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)

#一般ユーザに変更
def disable_admin(userID):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "user" SET admin = False WHERE userID = %s;
            """, (userID,))
        conn.commit()
        print(f"✅ アイコンを変更しました。")
    except psycopg2.Error as e:
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)



#コンテンツ詳細取得
def get_all_content_data(offset):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.contentID, c.spotlightnum, c.playnum, c.contentpath, c.thumbnailpath, c.title, c.tag, c.posttimestamp, 
                c.userID , u.username,
                COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum,
                COALESCE((SELECT COUNT(*) FROM reports WHERE contentID = c.contentID) ,0)AS reportnum
                FROM content c 
                LEFT OUTER JOIN "user" u ON c.userID = u.userID
                ORDER BY c.contentID ASC
                LIMIT 300 OFFSET %s;
                """
            ,(offset,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


#通報取得
def get_reports_data(offset):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.reportID, r.reporttype, r.reportuidID, u1.username, r.targetuidID, u2.username,
                r.contentID, r.comCTID, r.comCMID, cm.commenttext, c.title, r.processflag, r.reason, r.detail, r.reporttimestamp
                FROM reports r
                LEFT OUTER JOIN "user" u1 ON r.reportuidID = u1.userID
                LEFT OUTER JOIN "user" u2 ON r.targetuidID = u2.userID
                LEFT OUTER JOIN content c ON r.contentID = c.contentID
                LEFT OUTER JOIN comment cm ON r.comCTID = cm.contentID AND r.comCMID = cm.commentID
                ORDER BY reporttimestamp ASC
                LIMIT 300 OFFSET %s;
                """
            ,(offset,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


#通報を処理
def process_report(reportID):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE reports SET processflag = True WHERE reportID = %s;
            """, (reportID,))
        conn.commit()
    except psycopg2.Error as e:
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)

#通報を処理解除
def unprocess_report(reportID):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE reports SET processflag = False WHERE reportID = %s;
            """, (reportID,))
        conn.commit()
    except psycopg2.Error as e:
        print("データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)