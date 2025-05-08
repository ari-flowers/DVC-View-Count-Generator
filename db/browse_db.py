import os
from dotenv import load_dotenv
import sqlite3
import pandas as pd

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "vpn_rotation.db")

conn = sqlite3.connect(DB_PATH)

query = "SELECT * FROM servers ORDER BY name ASC;"
df = pd.read_sql_query(query, conn)

print(df.to_markdown(tablefmt='grid', index=False))

conn.close()