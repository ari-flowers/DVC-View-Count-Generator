import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "vpn_rotation.db")

def connect():
    return sqlite3.connect(DB_PATH)

# ----------------------------
# Server Table
# ----------------------------

def upsert_server(name, country=None, city=None, health=None, skip=False, skip_reason=None):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO servers (name, country, city, health, skip, skip_reason, last_status_check)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            country=excluded.country,
            city=excluded.city,
            health=excluded.health,
            skip=excluded.skip,
            skip_reason=excluded.skip_reason,
            last_status_check=excluded.last_status_check;
    """, (name, country, city, health, skip, skip_reason, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_usable_servers():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM servers WHERE skip = 0")
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def mark_server_skipped(name, reason="manual"):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE servers SET skip = 1, skip_reason = ?, last_status_check = ?
        WHERE name = ?
    """, (reason, datetime.utcnow().isoformat(), name))
    conn.commit()
    conn.close()

# ----------------------------
# Click Logs
# ----------------------------

def log_click(dragon_link, server_name, success=True):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM servers WHERE name = ?", (server_name,))
    result = cursor.fetchone()
    if not result:
        print(f"⚠️ Server '{server_name}' not found in DB.")
        conn.close()
        return
    server_id = result[0]
    cursor.execute("""
        INSERT INTO click_logs (dragon_link, server_id, timestamp, success)
        VALUES (?, ?, ?, ?)
    """, (dragon_link, server_id, datetime.utcnow().isoformat(), int(success)))
    conn.commit()
    conn.close()

def get_view_count_for_link(link):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM click_logs
        WHERE dragon_link = ? AND success = 1
    """, (link,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_used_servers_for_link(link):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.name
        FROM click_logs c
        JOIN servers s ON c.server_id = s.id
        WHERE c.dragon_link = ? AND c.success = 1
    """, (link,))
    results = {row[0] for row in cursor.fetchall()}
    conn.close()
    return results

# ----------------------------
# Dragon Link Personality Goals
# ----------------------------

def get_dragon_link_data(link):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT personality_goal, target_views
        FROM dragon_links
        WHERE link = ?
    """, (link,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"personality_goal": result[0], "target_views": result[1]}
    return None

def upsert_dragon_link(link, personality_goal=None, target_views=None):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO dragon_links (link, personality_goal, target_views)
        VALUES (?, ?, ?)
        ON CONFLICT(link) DO UPDATE SET
            personality_goal = excluded.personality_goal,
            target_views = excluded.target_views
    """, (link, personality_goal, target_views))
    conn.commit()
    conn.close()