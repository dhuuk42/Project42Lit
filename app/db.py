import os
import psycopg2
import hashlib
from dotenv import load_dotenv
from datetime import date

load_dotenv()

def get_conn():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    with get_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hash_password(password)))
                conn.commit()
                return True
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return False

def authenticate_user(username, password):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            if result and result[1] == hash_password(password):
                return result[0]
    return None

def insert_weight(user_id, date, weight):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO weight_entries (user_id, date, weight) VALUES (%s, %s, %s)", (user_id, date, weight))
            conn.commit()

def get_all_weights_for_all_users():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.username, w.date, w.weight
                FROM weight_entries w
                JOIN users u ON w.user_id = u.id
                ORDER BY w.date ASC
            """)
            return cur.fetchall()

def user_exists(username):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            return cur.fetchone() is not None

def register_test_users():
    users = [("alice", "alice123"), ("bob", "bob123")]
    for username, password in users:
        if not user_exists(username):
            register_user(username, password)

def init_challenge_table():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS challenge_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    date DATE NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    UNIQUE(user_id, date)
                )
            """)
            conn.commit()

def log_challenge_completion(user_id, challenge_date):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO challenge_log (user_id, date, completed) VALUES (%s, %s, TRUE) "
                "ON CONFLICT (user_id, date) DO UPDATE SET completed = TRUE",
                (user_id, challenge_date)
            )
            conn.commit()

def has_completed_challenge(user_id, challenge_date):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT completed FROM challenge_log WHERE user_id = %s AND date = %s",
                (user_id, challenge_date)
            )
            result = cur.fetchone()
            return result is not None and result[0]

def get_challenge_status_all_users(challenge_date):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.username, COALESCE(c.completed, FALSE)
                FROM users u
                LEFT JOIN challenge_log c ON u.id = c.user_id AND c.date = %s
                ORDER BY u.username
            """, (challenge_date,))
            return cur.fetchall()
def get_weights_for_user(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, date, weight
                FROM weight_entries
                WHERE user_id = %s
                ORDER BY date DESC
            """, (user_id,))
            return cur.fetchall()

def delete_weight_entry(entry_id, user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM weight_entries
                WHERE id = %s AND user_id = %s
            """, (entry_id, user_id))

