import psycopg2
import os

# DB接続設定
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def update_FMCtoken(new_token,uid):
    try:
        # PostgreSQLへ接続
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        # 登録処理
        cur.execute("UPDATE \"user\" SET token = %s WHERE userID = %s", (new_token, uid))
        conn.commit()
        cur.close()
        conn.close()
        print("tokenをアップデートしました。")

    except psycopg2.Error as e:
        print("データベースエラー:", e)

def get_user_by_id(userID):
    """ユーザーIDでユーザー情報を取得"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute('SELECT userID, username, iconimgpath, token, notificationenabled FROM "user" WHERE userID = %s', (userID,))
        row = cur.fetchone()
        
        if row:
            user = {
                "userID": row[0],
                "username": row[1],
                "iconimgpath": row[2],
                "token": row[3],
                "notificationenabled": row[4]
            }
        else:
            user = None
            
        cur.close()
        conn.close()
        return user
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return None

def user_exists(userID):
    """ユーザーが存在するか確認"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM "user" WHERE userID = %s', (userID,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return False

def get_user_name(userID):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute('SELECT username FROM "user" WHERE userID = %s', (userID,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(count["username"])
        return count["username"]
    except psycopg2.Error as e:
        print("データベースエラー:", e)
        return False