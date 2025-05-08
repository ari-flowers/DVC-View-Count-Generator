import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "vpn_rotation.db")

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    country TEXT,
    city TEXT,
    skip BOOLEAN DEFAULT 0,
    skip_reason TEXT,
    last_status_check TEXT,
    health TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS click_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dragon_link TEXT NOT NULL,
    server_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dragon_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link TEXT UNIQUE NOT NULL,
    personality_goal TEXT,
    target_views INTEGER,
    views_given INTEGER DEFAULT 0
);
""")

conn.commit()
conn.close()
print("✅ Database and schema created: vpn_rotation.db")