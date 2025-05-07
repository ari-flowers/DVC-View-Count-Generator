import os
import requests
import zipfile
import io
from dotenv import load_dotenv

CONFIG_DIR = "configs/"
SERVER_STATUS_URL = "https://airvpn.org/api/status/"
CONFIG_GENERATOR_URL = "https://airvpn.org/api/generator.zip"

load_dotenv()
API_KEY = os.getenv("AIRVPN_API_KEY")

def fetch_active_server_names():
    print("Fetching current AirVPN servers from API...")
    response = requests.get(SERVER_STATUS_URL, timeout=10)
    response.raise_for_status()
    data = response.json()

    servers = data["servers"]
    active_names = {server["public_name"] for server in servers if server.get("health") == "ok"}
    print(f"Found {len(active_names)} active servers.")
    return active_names

def get_local_config_names():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    files = os.listdir(CONFIG_DIR)
    ovpn_files = [f for f in files if f.endswith(".ovpn")]
    return {f.split("_")[2] for f in ovpn_files if len(f.split("_")) > 2}

def download_all_configs():
    print("Downloading latest AirVPN configs...")
    headers = {"User-Agent": "vpn-sync-bot"}
    params = {
        "protocol": "udp",
        "port": "443",
        "entry": "1",
        "compressed": "1",
        "format": "ovpn",
        "platform": "linux",
        "ipv6": "false",
        "dns": "true",
        "firewall": "false",
        "region": "world",
        "username": "",
        "token": API_KEY
    }

    response = requests.get(CONFIG_GENERATOR_URL, headers=headers, params=params, timeout=20)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        print("Unzipping configs...")
        z.extractall(CONFIG_DIR)
    print("Config files updated.")

def remove_stale_configs(active_server_names):
    print("Checking for stale configs...")
    for file in os.listdir(CONFIG_DIR):
        if not file.endswith(".ovpn"):
            continue
        parts = file.split("_")
        if len(parts) < 3:
            continue
        shortname = parts[2]
        if shortname not in active_server_names:
            os.remove(os.path.join(CONFIG_DIR, file))
            print(f"Removed stale config: {file}")

def sync_configs():
    try:
        active_servers = fetch_active_server_names()
        local_servers = get_local_config_names()

        missing = active_servers - local_servers
        stale = local_servers - active_servers

        print(f"Missing configs: {len(missing)}")
        print(f"Stale configs: {len(stale)}")

        download_all_configs()
        remove_stale_configs(active_servers)

    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to AirVPN API: {e}")

if __name__ == "__main__":
    sync_configs()