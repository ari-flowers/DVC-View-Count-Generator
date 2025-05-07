import os
import re
from db import upsert_server  # Make sure db.py is in the same directory or PYTHONPATH

CONFIG_DIR = "configs/"

# Regex pattern to extract: country, city, server
pattern = re.compile(
    r"AirVPN_([A-Z]{2})-([A-Za-z0-9\-]+)_([A-Za-z0-9]+)_UDP-\d+-Entry\d+\.ovpn"
)

def sync_servers_from_ovpn():
    if not os.path.exists(CONFIG_DIR):
        print(f"❌ Config directory '{CONFIG_DIR}' does not exist.")
        return

    files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".ovpn")]
    print(f"🔍 Found {len(files)} config files.")

    added = 0
    for f in files:
        match = pattern.match(f)
        if match:
            country, city, server = match.groups()
            upsert_server(
                name=server,
                country=country,
                city=city,
                health=None,
                skip=False,
                skip_reason=None
            )
            print(f"✅ Synced server: {server} ({country}-{city})")
            added += 1
        else:
            print(f"⚠️ Could not parse: {f}")

    print(f"\n✅ Done. Synced {added} servers to the database.")

if __name__ == "__main__":
    sync_servers_from_ovpn()