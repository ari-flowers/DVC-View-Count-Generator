# helpers/vpn.py

import os
import re
import requests
import subprocess
import threading
import time
from dotenv import load_dotenv
from db.db import mark_server_skipped, upsert_server

load_dotenv()

AIRVPN_API_KEY = os.getenv("AIRVPN_API_KEY")
AIRVPN_STATUS_URL = f"https://airvpn.org/api/status/?key={AIRVPN_API_KEY}&format=json"
AIRVPN_IP_CHECK_URL = f"https://airvpn.org/api/whatismyip/?key={AIRVPN_API_KEY}&format=json"
IPIFY_URL = "https://api.ipify.org?format=json"
CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "configs"))
if not os.path.isdir(CONFIG_DIR):
    print(f"❌ Config directory not found at: {CONFIG_DIR}")
MAX_TIMEOUT = 10

RAINBOW_COLORS = ["\033[91m", "\033[93m", "\033[92m", "\033[96m", "\033[94m", "\033[95m"]
RESET_COLOR = "\033[0m"


def extract_server_name(filename):
    pattern = re.compile(r"AirVPN_(?:[A-Z]{2}-[^_]+)_([A-Za-z0-9]+)_UDP-\d+-Entry\d+\.ovpn")
    match = pattern.match(filename)
    return match.group(1) if match else filename.split(".")[0]


def get_current_ip():
    try:
        response = requests.get(AIRVPN_IP_CHECK_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("airvpn") is True:
            return data.get("ip")
        else:
            raise ValueError("Not connected to AirVPN.")
    except:
        try:
            response = requests.get(IPIFY_URL, timeout=10)
            response.raise_for_status()
            return response.json().get("ip")
        except requests.RequestException as e:
            print(f"Error checking IP: {e}")
            return None


def server_is_healthy(server_name):
    try:
        response = requests.get(AIRVPN_STATUS_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        for server in data.get("servers", []):
            if server.get("public_name") == server_name:
                health = server.get("health")
                reason = server.get("warning") if health != "ok" else None

                if reason:
                    print(f"⚠️  {server_name} warning: {reason}")

                upsert_server(
                    name=server_name,
                    health=health,
                    skip=(health != "ok"),
                    skip_reason=reason
                )
                return health == "ok"
        print(f"⚠️ Server '{server_name}' not found in AirVPN API.")
        return False

    except requests.RequestException as e:
        print(f"🔌 Error fetching server health: {e}")
        return False


def connect_to_vpn(config_file):
    server_name = extract_server_name(config_file)
    if not server_is_healthy(server_name):
        mark_server_skipped(server_name, "unhealthy via API")
        return None

    print(f"🔁 Connecting to VPN server: {server_name}")

    command = f"sudo hummingbird {os.path.join(CONFIG_DIR, config_file)}"
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    connected = False

    def read_output():
        nonlocal connected
        for line in proc.stdout:
            if "EVENT: CONNECTED" in line:
                connected = True
                break

    thread = threading.Thread(target=read_output, daemon=True)
    thread.start()

    spinner = ['|', '/', '-', '\\']
    for i in range(MAX_TIMEOUT * 4):
        if connected:
            break
        color = RAINBOW_COLORS[i % len(RAINBOW_COLORS)]
        print(f"\r⏳ Connecting... {color}{spinner[i % len(spinner)]}{RESET_COLOR}", end="", flush=True)
        time.sleep(0.25)

    print("\r", end="")
    print()

    if connected:
        print(f"✅ Connected to {server_name}")
        return proc
    else:
        print(f"⛔ Connection timed out for {server_name}")
        proc.terminate()
        proc.wait()
        mark_server_skipped(server_name, "connection timeout")
        return None


def disconnect_vpn(proc):
    if proc:
        print("🔌 Disconnecting VPN...\n")
        proc.terminate()
        proc.wait()