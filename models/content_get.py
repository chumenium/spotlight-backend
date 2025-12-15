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
        # デバッグ用のprint文を削除（コスト削減のため）
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


#新しい順lastcontentid更新
def update_last_contetid_newest(uid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "user"
                SET lastcontetid = (
                    SELECT MAX(contentid) FROM content WHERE userID NOT IN (
                        SELECT blockedUserID
                        FROM blocklist
                        WHERE userID = %s
                        UNION
                        SELECT userID
                        FROM blocklist
                        WHERE blockedUserID = %s)
                ) WHERE userID = %s;
                """, (uid,uid,uid))
            cur.execute("""
                UPDATE "user"
                SET LMcontentID = (
                    SELECT MAX(contentid) FROM content WHERE userID NOT IN (
                        SELECT blockedUserID
                        FROM blocklist
                        WHERE userID = %s
                        UNION
                        SELECT userID
                        FROM blocklist
                        WHERE blockedUserID = %s)
                ) WHERE userID = %s;
                """, (uid,uid,uid))
            conn.commit()
        return True
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)

#最新投稿を取得
def get_content_latest_5(uid):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT LMcontentID FROM "user" WHERE userID = %s', (uid,)) 
            LMcontentID = cur.fetchone()
            if LMcontentID:
                LMcontentID = LMcontentID[0]
            else:
                LMcontentID = 1000000000
            cur.execute("""
                SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                    c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, c.textflag, c.thumbnailpath,
                    cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
                FROM content c
                JOIN "user" u1 ON c.userID = u1.userID
                LEFT JOIN contentuser cu 
                ON cu.contentID = c.contentID
                AND cu.userID = %s
                WHERE c.contentID > %s
                AND c.userID NOT IN (
                    SELECT blockedUserID
                    FROM blocklist
                    WHERE userID = %s
                    UNION
                    SELECT userID
                    FROM blocklist
                    WHERE blockedUserID = %s
                )
                ORDER BY c.contentID DESC
                LIMIT 5;
            """, (uid, LMcontentID, uid, uid))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)

#新しい順
def get_content_newest_5(uid, limitnum):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""SELECT lastcontetid, LMcontentID FROM "user" WHERE userID = %s""", (uid,))
            lastcontetid, LMcontentID = cur.fetchone()
            if lastcontetid == LMcontentID:
                lastcontetid += 1
            cur.execute("""
                SELECT c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                    c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, c.textflag, c.thumbnailpath,
                    cu.spotlightflag, COALESCE((SELECT COUNT(*) FROM comment WHERE contentID = c.contentID) ,0)AS commentnum, c.contentid
                FROM content c
                JOIN "user" u1 ON c.userID = u1.userID
                LEFT JOIN contentuser cu 
                ON cu.contentID = c.contentID
                AND cu.userID = %s
                WHERE c.contentID < (SELECT COALESCE(lastcontetid,0) FROM "user" WHERE userID = %s)
                AND c.userID NOT IN (
                    SELECT blockedUserID
                    FROM blocklist
                    WHERE userID = %s
                    UNION
                    SELECT userID
                    FROM blocklist
                    WHERE blockedUserID = %s
                )
                ORDER BY c.contentID DESC
                LIMIT %s;
            """, (uid, uid, uid, uid, limitnum))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)

#古い順
def get_content_oldest_5(uid):
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
                WHERE c.contentID > (SELECT COALESCE(lastcontetid,0) FROM "user" WHERE userID = %s)
                AND c.userID NOT IN (
                    SELECT blockedUserID
                    FROM blocklist
                    WHERE userID = %s
                    UNION
                    SELECT userID
                    FROM blocklist
                    WHERE blockedUserID = %s
                )
                ORDER BY c.contentID ASC
                LIMIT 5;
            """, (uid, uid, uid, uid))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return []
    finally:
        if conn:
            release_connection(conn)

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
    完全ランダムで5件取得（重複なし、ループ対応）
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
                    c.contentid
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
                LIMIT 5;
            """
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
        return rows
    except psycopg2.Error as e:
        print("データベースエラー(get_content_random_5):", e)
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
        print("データベースエラー(get_content_id_range):", e)
        return None, None, 0
    finally:
        if conn:
            release_connection(conn)

# 新着順：新着投稿を優先的に取得（最適化版・ループ対応）
def get_content_newest_with_priority(uid, limitnum=5, exclude_content_ids=None):
    """
    新着投稿を優先的に取得。新着投稿がない場合は通常の新着順で取得
    ループ対応（最後まで行ったら最初に戻る）
    片方向ブロック（自分がブロックしたユーザーのみ除外）
    視聴履歴直近50件を除外
    最適化: CTE使用、UNION ALLで1クエリに統合、コメント数はLEFT JOIN
    
    Args:
        uid: ユーザーID
        limitnum: 取得件数
        exclude_content_ids: 除外するコンテンツIDのリスト（スクロール中の重複防止用）
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # ユーザー状態を1回のクエリで取得
            cur.execute('SELECT lastcontetid, LMcontentID FROM "user" WHERE userID = %s', (uid,))
            user_state = cur.fetchone()
            lastcontetid = user_state[0] if user_state and user_state[0] else None
            LMcontentID = user_state[1] if user_state and user_state[1] else None
            
            # UNION ALLで新着投稿と通常の新着順を1クエリで取得
            params = [uid]  # blocked_users CTE用（片方向ブロック）
            
            # 除外IDの条件を構築
            exclude_condition = ""
            if exclude_content_ids and len(exclude_content_ids) > 0:
                placeholders = ','.join(['%s'] * len(exclude_content_ids))
                exclude_condition = f" AND c.contentID NOT IN ({placeholders})"
            
            # 視聴履歴直近50件の除外条件
            history_exclude_condition = """
                AND NOT EXISTS (
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
                    ) ph
                    WHERE ph.contentID = c.contentID
                )
            """
            
            # クエリパーツを構築
            query_parts = []
            
            # 新着投稿の条件（優先度1）
            if LMcontentID:
                query_parts.append("""
                    SELECT 
                        c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                        c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, 
                        c.textflag, c.thumbnailpath,
                        cu.spotlightflag, 
                        COALESCE(comment_counts.commentnum, 0) AS commentnum, 
                        c.contentid,
                        1 AS priority
                    FROM content c
                    JOIN "user" u1 ON c.userID = u1.userID
                    LEFT JOIN contentuser cu ON cu.contentID = c.contentID AND cu.userID = %s
                    LEFT JOIN (
                        SELECT contentID, COUNT(*) AS commentnum
                        FROM comment
                        GROUP BY contentID
                    ) comment_counts ON c.contentID = comment_counts.contentID
                    WHERE c.contentID > %s
                    AND (c.textflag = FALSE OR c.textflag IS NULL)
                    AND c.userID NOT IN (SELECT userID FROM blocked_users)
                """ + history_exclude_condition + exclude_condition)
                params.extend([uid, LMcontentID, uid])  # contentuser JOIN, LMcontentID, playhistory
                if exclude_content_ids and len(exclude_content_ids) > 0:
                    params.extend(exclude_content_ids)
            
            # 通常の新着順の条件（優先度2）
            if lastcontetid:
                query_parts.append("""
                    SELECT 
                        c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                        c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, 
                        c.textflag, c.thumbnailpath,
                        cu.spotlightflag, 
                        COALESCE(comment_counts.commentnum, 0) AS commentnum, 
                        c.contentid,
                        2 AS priority
                    FROM content c
                    JOIN "user" u1 ON c.userID = u1.userID
                    LEFT JOIN contentuser cu ON cu.contentID = c.contentID AND cu.userID = %s
                    LEFT JOIN (
                        SELECT contentID, COUNT(*) AS commentnum
                        FROM comment
                        GROUP BY contentID
                    ) comment_counts ON c.contentID = comment_counts.contentID
                    WHERE c.contentID < %s
                    AND (c.textflag = FALSE OR c.textflag IS NULL)
                    AND c.userID NOT IN (SELECT userID FROM blocked_users)
                """ + history_exclude_condition + exclude_condition)
                params.extend([uid, lastcontetid, uid])  # contentuser JOIN, lastcontetid, playhistory
                if exclude_content_ids and len(exclude_content_ids) > 0:
                    params.extend(exclude_content_ids)
            else:
                # lastcontetidがない場合は最初から取得
                query_parts.append("""
                    SELECT 
                        c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                        c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, 
                        c.textflag, c.thumbnailpath,
                        cu.spotlightflag, 
                        COALESCE(comment_counts.commentnum, 0) AS commentnum, 
                        c.contentid,
                        2 AS priority
                    FROM content c
                    JOIN "user" u1 ON c.userID = u1.userID
                    LEFT JOIN contentuser cu ON cu.contentID = c.contentID AND cu.userID = %s
                    LEFT JOIN (
                        SELECT contentID, COUNT(*) AS commentnum
                        FROM comment
                        GROUP BY contentID
                    ) comment_counts ON c.contentID = comment_counts.contentID
                    WHERE (c.textflag = FALSE OR c.textflag IS NULL)
                    AND c.userID NOT IN (SELECT userID FROM blocked_users)
                """ + history_exclude_condition + exclude_condition)
                params.extend([uid, uid])  # contentuser JOIN, playhistory
                if exclude_content_ids and len(exclude_content_ids) > 0:
                    params.extend(exclude_content_ids)
            
            # クエリが空の場合は空の結果を返す
            if not query_parts:
                return []
            
            # クエリ構築
            query = _get_one_way_blocked_users_cte() + """
                SELECT * FROM (
            """ + " UNION ALL ".join(query_parts) + """
                ) combined
                ORDER BY priority ASC, contentid DESC
                LIMIT %s;
            """
            params.append(limitnum)
            
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            
            # priorityカラムを除外して返す（後方互換性のため）
            return [row[:14] for row in rows]
    except psycopg2.Error as e:
        print("データベースエラー(get_content_newest_with_priority):", e)
        return []
    finally:
        if conn:
            release_connection(conn)

# 古い順：新着投稿を最後のキューに入れる（最適化版・ループ対応）
def get_content_oldest_with_newest_queue(uid, limitnum=5, exclude_content_ids=None):
    """
    古い順で取得。新着投稿があれば最後のキューに入れる
    ループ対応（最後まで行ったら最初に戻る）
    片方向ブロック（自分がブロックしたユーザーのみ除外）
    視聴履歴直近50件を除外
    最適化: CTE使用、UNION ALLで1クエリに統合、コメント数はLEFT JOIN
    
    Args:
        uid: ユーザーID
        limitnum: 取得件数
        exclude_content_ids: 除外するコンテンツIDのリスト（スクロール中の重複防止用）
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # ユーザー状態を1回のクエリで取得
            cur.execute('SELECT lastcontetid, LMcontentID FROM "user" WHERE userID = %s', (uid,))
            user_state = cur.fetchone()
            lastcontetid = user_state[0] if user_state and user_state[0] else None
            LMcontentID = user_state[1] if user_state and user_state[1] else None
            
            params = [uid]  # blocked_users CTE用（片方向ブロック）
            
            # 除外IDの条件を構築
            exclude_condition = ""
            if exclude_content_ids and len(exclude_content_ids) > 0:
                placeholders = ','.join(['%s'] * len(exclude_content_ids))
                exclude_condition = f" AND c.contentID NOT IN ({placeholders})"
            
            # 視聴履歴直近50件の除外条件
            history_exclude_condition = """
                AND NOT EXISTS (
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
                    ) ph
                    WHERE ph.contentID = c.contentID
                )
            """
            
            # クエリパーツを構築
            query_parts = []
            
            # 通常の古い順（優先度1）
            if lastcontetid:
                query_parts.append("""
                    SELECT 
                        c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                        c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, 
                        c.textflag, c.thumbnailpath,
                        cu.spotlightflag, 
                        COALESCE(comment_counts.commentnum, 0) AS commentnum, 
                        c.contentid,
                        1 AS priority
                    FROM content c
                    JOIN "user" u1 ON c.userID = u1.userID
                    LEFT JOIN contentuser cu ON cu.contentID = c.contentID AND cu.userID = %s
                    LEFT JOIN (
                        SELECT contentID, COUNT(*) AS commentnum
                        FROM comment
                        GROUP BY contentID
                    ) comment_counts ON c.contentID = comment_counts.contentID
                    WHERE c.contentID > %s
                    AND (c.textflag = FALSE OR c.textflag IS NULL)
                    AND c.userID NOT IN (SELECT userID FROM blocked_users)
                """ + history_exclude_condition + exclude_condition)
                params.extend([uid, lastcontetid, uid])  # contentuser JOIN, lastcontetid, playhistory
                if exclude_content_ids and len(exclude_content_ids) > 0:
                    params.extend(exclude_content_ids)
            else:
                # lastcontetidがない場合は最初から取得
                query_parts.append("""
                    SELECT 
                        c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                        c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, 
                        c.textflag, c.thumbnailpath,
                        cu.spotlightflag, 
                        COALESCE(comment_counts.commentnum, 0) AS commentnum, 
                        c.contentid,
                        1 AS priority
                    FROM content c
                    JOIN "user" u1 ON c.userID = u1.userID
                    LEFT JOIN contentuser cu ON cu.contentID = c.contentID AND cu.userID = %s
                    LEFT JOIN (
                        SELECT contentID, COUNT(*) AS commentnum
                        FROM comment
                        GROUP BY contentID
                    ) comment_counts ON c.contentID = comment_counts.contentID
                    WHERE (c.textflag = FALSE OR c.textflag IS NULL)
                    AND c.userID NOT IN (SELECT userID FROM blocked_users)
                """ + history_exclude_condition + exclude_condition)
                params.extend([uid, uid])  # contentuser JOIN, playhistory
                if exclude_content_ids and len(exclude_content_ids) > 0:
                    params.extend(exclude_content_ids)
            
            # 新着投稿を最後のキューに（優先度2）
            if LMcontentID:
                query_parts.append("""
                    SELECT 
                        c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                        c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, 
                        c.textflag, c.thumbnailpath,
                        cu.spotlightflag, 
                        COALESCE(comment_counts.commentnum, 0) AS commentnum, 
                        c.contentid,
                        2 AS priority
                    FROM content c
                    JOIN "user" u1 ON c.userID = u1.userID
                    LEFT JOIN contentuser cu ON cu.contentID = c.contentID AND cu.userID = %s
                    LEFT JOIN (
                        SELECT contentID, COUNT(*) AS commentnum
                        FROM comment
                        GROUP BY contentID
                    ) comment_counts ON c.contentID = comment_counts.contentID
                    WHERE c.contentID > %s
                    AND (c.textflag = FALSE OR c.textflag IS NULL)
                    AND c.userID NOT IN (SELECT userID FROM blocked_users)
                """ + history_exclude_condition + exclude_condition)
                params.extend([uid, LMcontentID, uid])  # contentuser JOIN, LMcontentID, playhistory
                if exclude_content_ids and len(exclude_content_ids) > 0:
                    params.extend(exclude_content_ids)
            
            # クエリが空の場合は空の結果を返す
            if not query_parts:
                return []
            
            # クエリ構築
            query = _get_one_way_blocked_users_cte() + """
                SELECT * FROM (
            """ + " UNION ALL ".join(query_parts) + """
                ) combined
                ORDER BY priority ASC, contentid ASC
                LIMIT %s;
            """
            params.append(limitnum)
            
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            
            # 不足分がある場合、ループして最初から取得
            if len(rows) < limitnum:
                loop_query = _get_one_way_blocked_users_cte() + """
                    SELECT 
                        c.title, c.contentpath, c.spotlightnum, c.posttimestamp, 
                        c.playnum, c.link, u1.username, u1.userID, u1.iconimgpath, 
                        c.textflag, c.thumbnailpath,
                        cu.spotlightflag, 
                        COALESCE(comment_counts.commentnum, 0) AS commentnum, 
                        c.contentid
                    FROM content c
                    JOIN "user" u1 ON c.userID = u1.userID
                    LEFT JOIN contentuser cu ON cu.contentID = c.contentID AND cu.userID = %s
                    LEFT JOIN (
                        SELECT contentID, COUNT(*) AS commentnum
                        FROM comment
                        GROUP BY contentID
                    ) comment_counts ON c.contentID = comment_counts.contentID
                    WHERE (c.textflag = FALSE OR c.textflag IS NULL)
                    AND c.userID NOT IN (SELECT userID FROM blocked_users)
                    AND NOT EXISTS (
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
                        ) ph
                        WHERE ph.contentID = c.contentID
                    )
                    ORDER BY c.contentID ASC
                    LIMIT %s;
                """
                cur.execute(loop_query, (uid, uid, uid, limitnum - len(rows)))
                loop_rows = cur.fetchall()
                rows = list(rows) + loop_rows
            
            # priorityカラムを除外して返す（後方互換性のため）
            return [row[:14] for row in rows[:limitnum]]
    except psycopg2.Error as e:
        print("データベースエラー(get_content_oldest_with_newest_queue):", e)
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