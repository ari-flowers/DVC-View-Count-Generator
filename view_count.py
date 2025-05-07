from helpers.scraper import fetch_live_view_count
import os
import re
import requests
import subprocess
import sys
import time
import signal
from datetime import datetime
import threading
from dotenv import load_dotenv

from db.db import (
    get_usable_servers,
    mark_server_skipped,
    log_click,
    upsert_server,
    get_used_servers_for_link,
    get_view_count_for_link,
)

# Load environment variables from .env
load_dotenv()
AIRVPN_API_KEY = os.getenv("AIRVPN_API_KEY")

# Configuration
CONFIG_DIR = "configs/"
MAX_TIMEOUT = 10
AIRVPN_STATUS_URL = f"https://airvpn.org/api/status/?key={AIRVPN_API_KEY}&format=json"
AIRVPN_IP_CHECK_URL = f"https://airvpn.org/api/whatismyip/?key={AIRVPN_API_KEY}&format=json"
IPIFY_URL = "https://api.ipify.org?format=json"

# Global for graceful shutdown
personal_ip = None
vpn_process = None

# --- Utility Functions ---

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

def graceful_exit(sig, frame):
    print("\n🛑 Graceful shutdown initiated...")
    if vpn_process:
        disconnect_vpn(vpn_process)
        print("🔄 Recovering network...")
        subprocess.run("sudo hummingbird --recover-network", shell=True)
    print("👋 Exiting program.")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

# --- AirVPN Server Health ---

def server_is_healthy(server_name):
    try:
        response = requests.get(AIRVPN_STATUS_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        for server in data.get("servers", []):
            if server.get("public_name") == server_name:
                health = server.get("health")
                reason = server.get("warning", None) if health != "ok" else None

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

# --- VPN Control ---

def connect_to_vpn(config_file):
    server_name = extract_server_name(config_file)
    if not server_is_healthy(server_name):
        mark_server_skipped(server_name, "unhealthy via API")
        return None

    print(f"🔁 Connecting to VPN server: {server_name}")

    command = f"sudo hummingbird {CONFIG_DIR}/{config_file}"
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    connected = False
    output_lines = []

    def read_output():
        nonlocal connected
        for line in proc.stdout:
            output_lines.append(line.strip())
            if "EVENT: CONNECTED" in line:
                connected = True
                break

    reader_thread = threading.Thread(target=read_output)
    reader_thread.daemon = True
    reader_thread.start()

    # Spinner
    spinner = ['|', '/', '-', '\\']
    rainbow_colors = [
        "\033[91m",  # Red
        "\033[93m",  # Yellow
        "\033[92m",  # Green
        "\033[96m",  # Cyan
        "\033[94m",  # Blue
        "\033[95m",  # Magenta
    ]
    RESET_COLOR = "\033[0m"

    for i in range(MAX_TIMEOUT * 4):  # 0.25s intervals
        if connected:
            break
        color = rainbow_colors[i % len(rainbow_colors)]
        print(f"\r{color}⏳ Connecting... {spinner[i % len(spinner)]}{RESET_COLOR}", end="", flush=True)
        time.sleep(0.25)

    print("\r", end="")  # Clear spinner line
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

# --- View Registration ---

def click_dragon_village_link(link):
    try:
        response = requests.get(link)
        return response.status_code == 200
    except requests.RequestException:
        return False

# --- Personality View Targets ---
PERSONALITY_VIEW_TARGETS = {
    "Silent": 0,
    "Solitary": 1,
    "Reserved": 5,      # Minimum required; target between 5-9
    "Mischievous": 50,  # Minimum required; target between 50-99
    "Lousy": 95,        # Minimum required; target between 95-99
    "Friendly": 100,   # Requires additional conditions
    "Extroverted": 100, # Requires additional conditions
    "Cute": 199,        # Requires additional conditions
    "Lovely": 200,
    "Arrogant": 200,    # Requires additional EV conditions  
}

def match_personality_input(user_input, personality_dict):
    user_input = user_input.lower()
    matches = [
        key for key in personality_dict
        if key.lower().startswith(user_input)
    ]
    if len(matches) == 1:
        return matches[0]  # Return the matched key
    elif len(matches) > 1:
        print(f"⚠️ Ambiguous input. Did you mean one of:")
        for m in matches:
            print(f" - {m}")
        return None
    else:
        print("❌ No matching personality found. Available options are:")
        for key in personality_dict:
            print(f" - {key}")
        return None

# --- Main ---
def main():
    global personal_ip, vpn_process

    # Set up graceful exit
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)

    # Initial IP check
    personal_ip = get_current_ip()
    if not personal_ip:
        print("❌ Could not determine your personal IP. Exiting.")
        return

    # User input
    dragon_link = input("Enter the Dragon Village link: ").strip()

    # 1. Fetch current view count from the live page
    live_views = fetch_live_view_count(dragon_link)
    if live_views is None:
        print("❌ Could not retrieve view count from page. Exiting.")
        return
    print(f"🔍 Live view count on page: {live_views}")

    # 2. Check if we've logged clicks before
    existing_views = get_view_count_for_link(dragon_link)
    if existing_views > 0:
        print(f"Views previously added: {existing_views}")

    # Prompt for desired personality
    personality_goal_input = input("Enter desired personality (or press Enter to skip): ").strip()
    if personality_goal_input:
        matched_goal = match_personality_input(personality_goal_input, PERSONALITY_VIEW_TARGETS)
        if not matched_goal:
            return
        personality_goal = matched_goal
        target_views = PERSONALITY_VIEW_TARGETS[personality_goal]
        print(f"🎯 Targeting personality '{personality_goal}' requires {target_views} total views.")
    else:
        try:
            target_views = int(input("Enter the number of total views you want: "))
            personality_goal = None  # Not targeting a personality
        except ValueError:
            print("❌ Invalid input.")
            return
        
    if target_views <= existing_views:
        print(f"✅ Already has {existing_views}/{target_views} views. No additional views needed.")
        return

    remaining_views = target_views - existing_views
    used_servers = get_used_servers_for_link(dragon_link)

    # Load configs and usable servers
    usable_servers = set(get_usable_servers())
    config_files = [
        f for f in os.listdir(CONFIG_DIR)
        if f.endswith(".ovpn") and extract_server_name(f) in usable_servers
    ]

    current_views = 0
    for config_file in config_files:
        server_name = extract_server_name(config_file)

        # Skip servers already used for this link
        if server_name in used_servers:
            continue

        if current_views >= remaining_views:
            break

        vpn_process = connect_to_vpn(config_file)

        if vpn_process:
            current_ip = get_current_ip()
            if current_ip and current_ip != personal_ip:
                print(f"🌐 VPN IP: {current_ip}")
                if click_dragon_village_link(dragon_link):
                    current_views += 1
                    print(f"***** ✅ Views: {existing_views + current_views}/{target_views} *****")
                    log_click(dragon_link, server_name, success=True)
                    used_servers.add(server_name)
                else:
                    print(f"❌ View failed via {server_name}")
                    log_click(dragon_link, server_name, success=False)
            disconnect_vpn(vpn_process)

    print(f"\n🎉 Done. {existing_views + current_views}/{target_views} views submitted.")

if __name__ == "__main__":
    main()