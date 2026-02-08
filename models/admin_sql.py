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
    except psycopg2.Error as e:
        pass
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
    except psycopg2.Error as e:
        pass
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
        pass
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
        pass
    finally:
        if conn:
            release_connection(conn)

#コンテンツ情報取得
def get_content_data(offset):
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
        return []
    finally:
        if conn:
            release_connection(conn)

#全ユーザのトークン取得（通知有効フラグ付き）
def get_all_user_token():
    """
    通知送信用に userID / token / notificationenabled を返す
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT userID, token, notificationenabled
                  FROM "user"
                 ORDER BY id ASC;
                """
            )
            rows = cur.fetchall()
        return [
            {
                "userID": row[0],
                "token": row[1],
                "notificationenabled": row[2],
            }
            for row in rows
        ]
    except psycopg2.Error:
        return []
    finally:
        if conn:
            release_connection(conn)

def statistics_data():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
            """
                SELECT COUNT(*) AS total_users,(SELECT COUNT(*) AS total_contents
                FROM content)
                FROM "user";
            """
            ,())
            rows = cur.fetchall()
        return rows
    except psycopg2.Error:
        return []
    finally:
        if conn:
            release_connection(conn)


# ID降順で最新ユーザーを取得（最大10件）
def get_users_desc_limit10(offset):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT userID, username, iconimgpath, id
                  FROM "user"
                 ORDER BY id DESC
                 LIMIT 10 OFFSET %s;
                """
            ,(offset,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error:
        return []
    finally:
        if conn:
            release_connection(conn)


# ID降順で最新コンテンツを取得（最大10件）
def get_contents_desc_limit10(offset):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT contentID, userID, title, contentpath, thumbnailpath, posttimestamp
                  FROM content
                 ORDER BY id DESC
                 LIMIT 10 OFFSET %s;
                """
            ,(offset,))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error:
        return []
    finally:
        if conn:
            release_connection(conn)


# 通報されているコンテンツ一覧を取得
def get_reported_contents():
    """
    reports.contentID に紐づく通報があるコンテンツを取得
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    c.contentID,
                    c.userID,
                    u.username,
                    c.title,
                    c.contentpath,
                    c.thumbnailpath,
                    COUNT(r.reportID) AS report_count
                FROM reports r
                JOIN content c ON r.contentID = c.contentID
                LEFT JOIN "user" u ON c.userID = u.userID
                GROUP BY c.contentID, c.userID, u.username, c.title, c.contentpath, c.thumbnailpath
                ORDER BY report_count DESC, c.contentID DESC;
                """
            )
            rows = cur.fetchall()
        return rows
    except psycopg2.Error:
        return []
    finally:
        if conn:
            release_connection(conn)


# 通報されているコメント一覧を取得
def get_reported_comments():
    """
    reports.comCTID / comCMID に紐づく通報があるコメントを取得
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    cm.contentID,
                    cm.commentID,
                    cm.userID,
                    u.username,
                    cm.commenttext,
                    COUNT(r.reportID) AS report_count
                FROM reports r
                JOIN comment cm
                  ON r.comCTID = cm.contentID
                 AND r.comCMID = cm.commentID
                LEFT JOIN "user" u ON cm.userID = u.userID
                GROUP BY cm.contentID, cm.commentID, cm.userID, u.username, cm.commenttext
                ORDER BY report_count DESC, cm.commentID DESC;
                """
            )
            rows = cur.fetchall()
        return rows
    except psycopg2.Error:
        return []
    finally:
        if conn:
            release_connection(conn)