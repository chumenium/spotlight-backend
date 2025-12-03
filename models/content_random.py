import psycopg2
from models.connection_pool import get_connection, release_connection


def get_recent_history_ids(uid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.contentid, c.title
                FROM content c
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
                    ) p
                    WHERE p.contentID = c.contentID
                )
                ORDER BY RANDOM()
                LIMIT 3;
            """, (uid,uid))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)


# SELECT DISTINCT contentID
# FROM (
#     SELECT contentID
#     FROM playhistory
#     WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
#     ORDER BY playid DESC
#     LIMIT 50
# ) AS recent_history
# UNION
# SELECT lastcontetid
# FROM "user"
# WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2';


# SELECT c.contentid, c.title
# FROM content c
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
#     ) p
#     WHERE p.contentID = c.contentID
# )
# ORDER BY RANDOM()
# LIMIT 3;