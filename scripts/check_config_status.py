# Run this first to check the status of your AirVPN configs, then run the sync script to update the database with any new servers.

import os
import sys
import requests
import argparse
from dotenv import load_dotenv
# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.db import upsert_server

CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "configs"))
AIRVPN_STATUS_URL = "https://airvpn.org/api/status/"

load_dotenv()

# --- Utility ---
def parse_server_name_from_config(filename):
    import re
    pattern = re.compile(r"AirVPN_[A-Z]{2}-[^_]+_([A-Za-z0-9]+)_UDP-\d+-Entry\d+\.ovpn")
    match = pattern.match(filename)
    return match.group(1) if match else None

def get_local_server_names():
    return {
        parse_server_name_from_config(f)
        for f in os.listdir(CONFIG_DIR)
        if f.endswith(".ovpn") and parse_server_name_from_config(f)
    }

def fetch_remote_server_names():
    print("\U0001F310 Fetching server status from AirVPN API...")
    try:
        response = requests.get(AIRVPN_STATUS_URL, timeout=10)
        response.raise_for_status()
        servers = response.json().get("servers", [])
        return {srv["public_name"] for srv in servers if srv.get("public_name")}
    except requests.RequestException as e:
        print(f"❌ Error fetching server data: {e}")
        return set()

# --- Main Logic ---
def check_config_status(delete=False):
    local = get_local_server_names()
    remote = fetch_remote_server_names()

    new_servers = remote - local
    stale_configs = local - remote

    print("\n\U0001F50D Config status:")
    print(f" - Total local configs: {len(local)}")
    print(f" - Total remote servers: {len(remote)}")
    print(f" - New servers available: {len(new_servers)}")
    print(f" - Stale configs: {len(stale_configs)}")

    if new_servers:
        print("\n🆕 New servers (not in your configs):")
        for name in sorted(new_servers):
            print(f" - {name}")

    if stale_configs:
        print("\n⚠️ Stale config files:")
        for name in sorted(stale_configs):
            print(f" - {name}")

        if not delete:
            confirm = input("\n🧹 Do you want to delete these stale configs now? (y/n): ").strip().lower()
            delete = confirm == 'y'

        if delete:
            print("\n🗑 Deleting stale configs...")
            for f in os.listdir(CONFIG_DIR):
                server = parse_server_name_from_config(f)
                if server in stale_configs:
                    os.remove(os.path.join(CONFIG_DIR, f))
                    print(f" - Deleted {f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check AirVPN config status")
    parser.add_argument("--delete", action="store_true", help="Auto-delete stale configs without prompt")
    args = parser.parse_args()

    check_config_status(delete=args.delete)