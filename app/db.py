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

def insert_weight(user_id, date, weight, note=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO weight_entries (user_id, date, weight, note) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (user_id, date) DO UPDATE SET weight = EXCLUDED.weight, note = EXCLUDED.note, created_at = NOW()",
                (user_id, date, weight, note)
            )
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
            cur.execute(
                """
                SELECT id, date, weight, note, created_at
                FROM weight_entries
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            return cur.fetchall()

def delete_weight_entry(entry_id, user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM weight_entries
                WHERE id = %s AND user_id = %s
            """, (entry_id, user_id))

def add_weight_entry(conn, user_id, date, weight, note=None):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO weight_entries (user_id, date, weight, note)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, date) DO UPDATE
            SET weight = EXCLUDED.weight,
                note = EXCLUDED.note,
                created_at = NOW()
            """,
            (user_id, date, weight, note)
        )
        conn.commit()

def get_weight_entries(conn, user_id, start_date=None, end_date=None):
    with conn.cursor() as cur:
        query = """
            SELECT id, date, weight, note, created_at
            FROM weight_entries
            WHERE user_id = %s
        """
        params = [user_id]
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        query += " ORDER BY created_at DESC"
        cur.execute(query, params)
        return cur.fetchall()

def change_password(user_id, new_password):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (hash_password(new_password), user_id)  # <-- hash the new password!
                )
                conn.commit()
        return True
    except Exception:
        return False

def get_user_color(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT color FROM users WHERE id = %s", (user_id,))
            result = cur.fetchone()
            return result[0] if result else None

def set_user_color(user_id, color):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET color = %s WHERE id = %s", (color, user_id))
            conn.commit()

def get_all_user_colors():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT username, color FROM users")
            return dict(cur.fetchall())

