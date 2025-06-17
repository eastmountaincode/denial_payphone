import sqlite3
import os
from datetime import datetime
from config.constants import DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "sessions.db")

def insert_session(session_id: str):
    """
    Insert a new session record into the database.
    Assumes the database and table already exist.
    """
    try:
        now = datetime.now()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (session_id, date, time)
                VALUES (?, ?, ?)
            ''', (session_id, now.date().isoformat(), now.time().isoformat()))
            conn.commit()
            print(f"Inserted session: {session_id}")
    except Exception as e:
        print(f"Error inserting session: {e}") 