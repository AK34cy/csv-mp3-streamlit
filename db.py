import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

DDL_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

DDL_FILES = """
CREATE TABLE IF NOT EXISTS user_files (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'csv',
    data BYTEA NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON user_files(user_id);
"""

def get_conn():
    url = os.getenv("POSTGRES_URL")
    if not url:
        raise RuntimeError("POSTGRES_URL не задан в .env")
    if "sslmode" not in url:
        url = url + ("&sslmode=require" if "?" in url else "?sslmode=require")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    return conn

def init_db(conn):
    with conn.cursor() as cur:
        cur.execute(DDL_USERS)
        cur.execute(DDL_FILES)

def get_user_by_email(conn, email: str):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        return cur.fetchone()

def create_user(conn, email: str, name: str, password_hash: str):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s) RETURNING *",
            (email, name, password_hash),
        )
        return cur.fetchone()

def store_file(conn, user_id: int, filename: str, data: bytes, kind: str = "csv"):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO user_files (user_id, filename, kind, data) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_id, filename, kind, psycopg2.Binary(data)),
        )
        return cur.fetchone()["id"]

def list_user_files(conn, user_id: int, kind: str | None = None):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if kind:
            cur.execute(
                "SELECT id, filename, kind, created_at FROM user_files WHERE user_id=%s AND kind=%s ORDER BY created_at DESC",
                (user_id, kind),
            )
        else:
            cur.execute(
                "SELECT id, filename, kind, created_at FROM user_files WHERE user_id=%s ORDER BY created_at DESC",
                (user_id,),
            )
        return cur.fetchall()

def get_file(conn, file_id: int, user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT filename, kind, data FROM user_files WHERE id=%s AND user_id=%s",
            (file_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        filename, kind, data = row
        return {"filename": filename, "kind": kind, "data": bytes(data)}
