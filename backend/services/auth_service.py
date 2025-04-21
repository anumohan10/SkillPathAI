import bcrypt
import uuid
from backend.database import get_snowflake_connection

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_user_id():
    return str(uuid.uuid4())

def create_users_table():
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id STRING PRIMARY KEY,
                    name VARCHAR(100),
                    username VARCHAR(100) UNIQUE,
                    email VARCHAR(255) UNIQUE,
                    password VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
                );
            """)
            conn.commit()
        finally:
            cur.close()
            conn.close()

def insert_user(name, username, email, hashed_password):
    user_id = generate_user_id()
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (user_id, name, username, email, password)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, name, username, email, hashed_password))
            conn.commit()
        finally:
            cur.close()
            conn.close()
    return user_id

def update_user_password(username, new_hashed_password):
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE users
                SET password = %s
                WHERE username = %s
            """, (new_hashed_password, username))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating password for {username}: {e}")
            return False
        finally:
            cur.close()
            conn.close()
    return False
def get_user_profile_by_username(username):
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, name, username, email, created_at
                FROM users
                WHERE username = %s
            """, (username,))
            row = cur.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "name": row[1],
                    "username": row[2],
                    "email": row[3],
                    "created_at": row[4]
                }
        finally:
            cur.close()
            conn.close()
    return None

def get_user_by_username(username):
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT user_id, name, email, password FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "password": row[3]
                }
        finally:
            cur.close()
            conn.close()
    return None
