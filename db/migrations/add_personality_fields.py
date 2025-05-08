import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "vpn_rotation.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add 'personality_goal' column if it doesn't exist
    cursor.execute("PRAGMA table_info(dragon_links);")
    columns = [col[1] for col in cursor.fetchall()]
    if 'personality_goal' not in columns:
        cursor.execute("ALTER TABLE dragon_links ADD COLUMN personality_goal TEXT;")

    # Add 'target_views' column if it doesn't exist
    if 'target_views' not in columns:
        cursor.execute("ALTER TABLE dragon_links ADD COLUMN target_views INTEGER;")

    conn.commit()
    conn.close()
    print("✅ Migration completed: Added 'personality_goal' and 'target_views' columns.")

if __name__ == "__main__":
    migrate()