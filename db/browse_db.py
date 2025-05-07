import sqlite3
import pandas as pd

conn = sqlite3.connect("vpn_rotation.db")

query = "SELECT * FROM servers ORDER BY name ASC;"
df = pd.read_sql_query(query, conn)

print(df.to_markdown(tablefmt='grid', index=False))

conn.close()