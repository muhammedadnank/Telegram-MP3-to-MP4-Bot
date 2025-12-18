import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Connection pool to manage connections efficiently
postgreSQL_pool = None

def init_pool():
    global postgreSQL_pool
    try:
        if not postgreSQL_pool:
            postgreSQL_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
            if postgreSQL_pool:
                print("Connection pool created successfully")
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error while connecting to PostgreSQL", error)

def get_connection():
    if not postgreSQL_pool:
        init_pool()
    return postgreSQL_pool.getconn()

def put_connection(conn):
    if postgreSQL_pool:
        postgreSQL_pool.putconn(conn)

def init_db():
    init_pool()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Table for active tasks to prevent multiple processing for one user
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    user_id BIGINT PRIMARY KEY,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Table for usage logs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    finally:
        put_connection(conn)

def add_task(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO tasks (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
            conn.commit()
    finally:
        put_connection(conn)

def remove_task(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE user_id = %s", (user_id,))
            conn.commit()
    finally:
        put_connection(conn)

def can_process(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM tasks WHERE user_id = %s", (user_id,))
            return cur.fetchone() is None
    finally:
        put_connection(conn)

def cleanup_old_data(hours=24):
    """Cleanup stuck tasks and old logs."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE started_at < NOW() - INTERVAL '1 hour'")
            cur.execute("DELETE FROM usage_logs WHERE timestamp < NOW() - INTERVAL '%s hours'", (hours,))
            conn.commit()
    finally:
        put_connection(conn)

def log_action(user_id, action):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO usage_logs (user_id, action) VALUES (%s, %s)", (user_id, action))
            conn.commit()
    finally:
        put_connection(conn)

def get_stats():
    """Retrieve bot usage statistics."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM tasks")
            active_tasks = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM usage_logs WHERE action = 'CONVERSION_SUCCESS'")
            total_conversions = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(DISTINCT user_id) FROM usage_logs")
            unique_users = cur.fetchone()[0]
            
            return {
                "active_tasks": active_tasks,
                "total_conversions": total_conversions,
                "unique_users": unique_users
            }
    finally:
        put_connection(conn)

def get_all_users():
    """Retrieve all unique user IDs for broadcasting."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT user_id FROM usage_logs")
            rows = cur.fetchall()
            return [row[0] for row in rows]
    finally:
        put_connection(conn)

def clear_all_tasks():
    """Emergency: Clear all processing tasks from DB."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE tasks")
            conn.commit()
    finally:
        put_connection(conn)
