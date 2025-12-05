import psycopg2
from models.connection_pool import get_connection, release_connection


def get_recent_history_ids(uid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                    c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, c.textflag, c.thumbnailpath,
                    cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
                FROM content c
                JOIN "user" u1 ON c.userID = u1.userID
                LEFT JOIN contentuser cu 
                ON cu.contentID = c.contentID
                AND cu.userID = %s
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM (
                        SELECT DISTINCT contentID
                        FROM (
                            SELECT contentID
                            FROM playhistory
                            WHERE userID = %s
                            ORDER BY playid DESC
                            LIMIT 50
                        ) AS recent_history
                        UNION
                        SELECT lastcontetid
                        FROM "user"
                        WHERE userID = %s
                        UNION
                        SELECT c.contentID
                        FROM content c
                        JOIN "user" u ON c.userID = u.userID
                        WHERE c.userID IN (
                            SELECT blockedUserID
                            FROM blocklist
                            WHERE userID = %s
                            UNION
                            SELECT userID
                            FROM blocklist
                            WHERE blockedUserID = %s
                        )
                    ) p
                    WHERE p.contentID = c.contentID
                )
                ORDER BY RANDOM()
                LIMIT 5;
            """, (uid,uid,uid,uid,uid))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)

def get_history_ran(uid,limitnum, exclude_content_ids=None):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # 除外するcontentIDの条件を追加
            exclude_condition = ""
            params = [uid, uid, uid, uid]
            
            if exclude_content_ids and len(exclude_content_ids) > 0:
                # 除外するcontentIDのプレースホルダーを作成
                placeholders = ','.join(['%s'] * len(exclude_content_ids))
                exclude_condition = f"""
                        UNION
                        SELECT contentID
                        FROM (VALUES ({placeholders})) AS excluded(contentID)
                """
                params.extend(exclude_content_ids)
            
            query = """
                SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                    c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, c.textflag, c.thumbnailpath,
                    cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
                FROM content c
                JOIN "user" u1 ON c.userID = u1.userID
                LEFT JOIN contentuser cu 
                ON cu.contentID = c.contentID
                AND cu.userID = %s
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM (
                        SELECT lastcontetid AS contentID
                        FROM "user"
                        WHERE userID = %s AND lastcontetid IS NOT NULL
                        UNION
                        SELECT DISTINCT contentID
                        FROM content
                        WHERE userID IN (
                            SELECT blockedUserID FROM blocklist WHERE userID = %s
                            UNION
                            SELECT userID FROM blocklist WHERE blockedUserID = %s
                        )
                    ) p
                    WHERE p.contentID = c.contentID
                )
            """
            # 除外するcontentIDがある場合は追加条件を適用
            if exclude_content_ids and len(exclude_content_ids) > 0:
                query += " AND c.contentID NOT IN (" + ','.join(['%s'] * len(exclude_content_ids)) + ")"
                params.extend(exclude_content_ids)
            
            query += " ORDER BY RANDOM() LIMIT %s;"
            params.append(limitnum)
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)

def update_last_contetid(uid,contentid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "user"
                SET lastcontetid = %s
                WHERE userID = %s;
            """, (contentid,uid))
        conn.commit()
        print("✅ 最終コンテンツID更新",contentid)
    except psycopg2.Error as e:
        print("❌ データベースエラー:", e)
    finally:
        if conn:
            release_connection(conn)

def get_one_content(uid,contentid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                    c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, c.textflag, c.thumbnailpath,
                    cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
                FROM content c
                JOIN "user" u1 ON c.userID = u1.userID
                LEFT JOIN contentuser cu 
                ON cu.contentID = c.contentID
                AND cu.userID = %s
                WHERE c.contentID = %s;
            """, (uid,contentid))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)

# SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
#        c.playnum, c.link, u1.username, u1.iconimgpath, c.textflag, c.thumbnailpath,
#        cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
# FROM content c
# JOIN "user" u1 ON c.userID = u1.userID
# LEFT JOIN contentuser cu 
#     ON cu.contentID = c.contentID
#     AND cu.userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
# WHERE NOT EXISTS (
#     SELECT 1
#     FROM (
#         SELECT lastcontetid AS contentID
#         FROM "user"
#         WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2' AND lastcontetid IS NOT NULL
#         UNION
#         SELECT DISTINCT contentID
#         FROM content
#         WHERE userID IN (
#             SELECT blockedUserID FROM blocklist WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
#             UNION
#             SELECT userID FROM blocklist WHERE blockedUserID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
#         )
#     ) p
#     WHERE p.contentID = c.contentID
# )
# ORDER BY RANDOM()
# LIMIT 5;


# SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
#        c.playnum, c.link, u1.username, u1.iconimgpath, c.textflag, c.thumbnailpath,
#        cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
# FROM content c
# JOIN "user" u1 ON c.userID = u1.userID
# WHERE NOT EXISTS (
#     SELECT 1
#     FROM (
#         SELECT DISTINCT contentID
#         FROM (
#             SELECT contentID
#             FROM playhistory
#             WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
#             ORDER BY playid DESC
#             LIMIT 50
#         ) AS recent_history
#         UNION
#         SELECT lastcontetid
#         FROM "user"
#         WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
#         UNION
#         SELECT c.contentID
#         FROM content c
#         JOIN "user" u ON c.userID = u.userID
#         WHERE c.userID IN (
#             SELECT blockedUserID
#             FROM blocklist
#             WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
#             UNION
#             SELECT userID
#             FROM blocklist
#             WHERE blockedUserID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
#         )
#     ) p
#     WHERE p.contentID = c.contentID
# )
# ORDER BY RANDOM()
# LIMIT 5;

# SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
#     c.playnum, c.link, u1.username, u1.iconimgpath, c.textflag, c.thumbnailpath,
#     cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
# FROM content c
# JOIN "user" u1 ON c.userID = u1.userID
# LEFT JOIN contentuser cu 
#     ON cu.contentID = c.contentID
#     AND cu.userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
# WHERE c.contentID = 3;