import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "vpn_rotation.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def print_table_schema(table):
    print(f"\n📄 Schema for table: {table}")
    cursor.execute(f"PRAGMA table_info({table});")
    columns = cursor.fetchall()
    if not columns:
        print("⚠️  No such table or empty schema.")
    else:
        for col in columns:
            cid, name, ctype, notnull, default, pk = col
            print(f" - {name} ({ctype}) {'PRIMARY KEY' if pk else ''}")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

if not tables:
    print("❌ No tables found in the database.")
else:
    print(f"📋 Tables found: {', '.join(tables)}")
    for table in tables:
        print_table_schema(table)

conn.close()