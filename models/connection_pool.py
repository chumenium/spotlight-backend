# spotlight-backend/models/db.py

from psycopg2 import pool
import psycopg2
import os

# グローバル変数としてプールを保持
connection_pool = None

def init_connection_pool():
    """Flask起動時に一度だけ呼び出してプールを作成"""
    global connection_pool
    if connection_pool is None:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=5,
            maxconn=20,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME")
        )
        print("✅ Connection pool created")
    else:
        print("ℹ️ Connection pool already exists")

def get_connection():
    """プールからコネクションを取得"""
    if connection_pool is None:
        raise Exception("❌ Connection pool is not initialized. Call init_connection_pool() first.")
    return connection_pool.getconn()

def release_connection(conn):
    """使用後にコネクションを返却"""
    if connection_pool:
        connection_pool.putconn(conn)

def close_all_connections():
    """アプリ終了時に全コネクションを閉じる"""
    if connection_pool:
        connection_pool.closeall()
        print("🛑 All connections closed")
