import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "vpn_rotation.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check if 'personality' column already exists
cursor.execute("PRAGMA table_info(click_logs);")
columns = [col[1] for col in cursor.fetchall()]

if 'personality' not in columns:
    cursor.execute("""
        ALTER TABLE click_logs ADD COLUMN personality TEXT;
    """)
    print("✅ Migration complete: Added 'personality' column to 'click_logs' table.")
else:
    print("ℹ️ Column 'personality' already exists. No changes made.")

conn.commit()
conn.close()