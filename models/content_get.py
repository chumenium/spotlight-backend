import psycopg2
from models.connection_pool import get_connection, release_connection


def get_recent_history_ids(uid, exclude_content_ids=None):
    """
    最近の再生履歴を除外してコンテンツを取得
    スクロール中の重複取得を防ぐため、既に取得したコンテンツIDを除外可能
    
    Args:
        uid: ユーザーID
        exclude_content_ids: 除外するコンテンツIDのリスト（スクロール中の重複防止用）
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # パラメータ構築
            params = [uid, uid, uid, uid, uid]
            
            # 除外IDの条件を追加
            exclude_condition = ""
            if exclude_content_ids and len(exclude_content_ids) > 0:
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
            """ + exclude_condition + """
                    ) p
                    WHERE p.contentID = c.contentID
                )
            """
            
            # 除外IDがある場合は追加条件を適用
            if exclude_content_ids and len(exclude_content_ids) > 0:
                query += " AND c.contentID NOT IN (" + ','.join(['%s'] * len(exclude_content_ids)) + ")"
                params.extend(exclude_content_ids)
            
            query += " ORDER BY RANDOM() LIMIT 5;"
            
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
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
    except psycopg2.Error as e:
        pass
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
        return []
    finally:
        if conn:
            release_connection(conn)


#新しい順lastcontentid更新

# ========================================
# 共通：ブロックリスト取得（CTEで最適化）
# ========================================
def _get_blocked_users_cte():
    """
    ブロックリストを取得するCTE（Common Table Expression）
    両方向ブロック（自分がブロックしたユーザー + 自分をブロックしたユーザー）
    パフォーマンス向上のため、サブクエリをCTEに変更
    """
    return """
        WITH blocked_users AS (
            SELECT blockedUserID AS userID
            FROM blocklist
            WHERE userID = %s
            UNION
            SELECT userID
            FROM blocklist
            WHERE blockedUserID = %s
        )
    """

def _get_one_way_blocked_users_cte():
    """
    片方向ブロックリストを取得するCTE（Common Table Expression）
    自分がブロックしたユーザーのみを除外
    パフォーマンス向上のため、サブクエリをCTEに変更
    """
    return """
        WITH blocked_users AS (
            SELECT blockedUserID AS userID
            FROM blocklist
            WHERE userID = %s
        )
    """

# ========================================
# 完全ランダム取得（最適化版）
# ========================================
def get_content_random_5(uid, exclude_content_ids=None):
    """
    完全ランダムで3件取得（重複なし、ループ対応）
    片方向ブロック（自分がブロックしたユーザーのみ除外）
    最適化: CTE使用、コメント数はLEFT JOINで取得
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # パラメータ構築
            params = [uid]  # blocked_users CTE用（片方向ブロック）
            
            # 除外IDの条件
            exclude_condition = ""
            if exclude_content_ids and len(exclude_content_ids) > 0:
                placeholders = ','.join(['%s'] * len(exclude_content_ids))
                exclude_condition = f" AND c.contentID NOT IN ({placeholders})"
                params.extend(exclude_content_ids)
            
            params.extend([uid])  # contentuser JOIN用
            
            query = _get_one_way_blocked_users_cte() + """
                SELECT 
                    c.title, 
                    c.contentpath, 
                    c.spotlightnum, 
                    c.posttimestamp, 
                    c.playnum, 
                    c.link, 
                    u1.username, 
                    u1.userID, 
                    u1.iconimgpath, 
                    c.textflag, 
                    c.thumbnailpath,
                    cu.spotlightflag, 
                    COALESCE(comment_counts.commentnum, 0) AS commentnum, 
                    COALESCE(c.contentID, 0) AS contentID
                FROM content c
                JOIN "user" u1 ON c.userID = u1.userID
                LEFT JOIN contentuser cu 
                    ON cu.contentID = c.contentID AND cu.userID = %s
                LEFT JOIN (
                    SELECT contentID, COUNT(*) AS commentnum
                    FROM comment
                    GROUP BY contentID
                ) comment_counts ON c.contentID = comment_counts.contentID
                WHERE (c.textflag = FALSE OR c.textflag IS NULL)
                AND c.userID NOT IN (SELECT userID FROM blocked_users)
            """ + exclude_condition + """
                ORDER BY RANDOM()
                LIMIT 3;
            """
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        return []
    finally:
        if conn:
            release_connection(conn)

# 最小・最大のcontentIDを取得（ループ判定用・最適化版）
def get_content_id_range(uid):
    """
    ユーザーが閲覧可能なコンテンツの最小・最大contentIDを取得
    片方向ブロック（自分がブロックしたユーザーのみ除外）
    最適化: CTE使用
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            query = _get_one_way_blocked_users_cte() + """
                SELECT MIN(c.contentID), MAX(c.contentID), COUNT(*)
                FROM content c
                WHERE (c.textflag = FALSE OR c.textflag IS NULL)
                AND c.userID NOT IN (SELECT userID FROM blocked_users)
            """
            cur.execute(query, (uid,))
            row = cur.fetchone()
        return (row[0], row[1], row[2]) if row else (None, None, 0)
    except psycopg2.Error as e:
        return None, None, 0
    finally:
        if conn:
            release_connection(conn)

# 削除済み: 新着順・古い順の関数群（不要になったため削除）
# - get_content_newest_with_priority
# - get_content_oldest_with_newest_queue

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


# SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
#     c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, c.textflag, c.thumbnailpath,
#     cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
# FROM content c
# JOIN "user" u1 ON c.userID = u1.userID
# LEFT JOIN contentuser cu 
# ON cu.contentID = c.contentID
# AND cu.userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
# WHERE c.contentID > (SELECT COALESCE(lastcontetid,0) FROM "user" WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2')
# AND c.userID NOT IN (
#     SELECT blockedUserID
#     FROM blocklist
#     WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
#     UNION
#     SELECT userID
#     FROM blocklist
#     WHERE blockedUserID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
# )
# ORDER BY c.contentID ASC
# LIMIT 5;


# SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
#     c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, c.textflag, c.thumbnailpath,
#     cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
# FROM content c
# JOIN "user" u1 ON c.userID = u1.userID
# LEFT JOIN contentuser cu 
# ON cu.contentID = c.contentID
# AND cu.userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
# WHERE c.contentID < (SELECT COALESCE(lastcontetid,0) FROM "user" WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2')
# AND c.userID NOT IN (
#     SELECT blockedUserID
#     FROM blocklist
#     WHERE userID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
#     UNION
#     SELECT userID
#     FROM blocklist
#     WHERE blockedUserID = '24m1kumuhUaYZOKyH3YraLLzFnX2'
# )
# ORDER BY c.contentID DESC
# LIMIT 5;