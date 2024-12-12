import os
import json
import requests
import subprocess
import time
import sys
import signal
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
AIRVPN_API_KEY = os.getenv("AIRVPN_API_KEY")

# Paths and file names
config_dir = "configs/"
log_file = "vpn_usage_log.json"
skip_list_file = "vpn_skip_list.json"
MAX_TIMEOUT = 10  # Timeout after x seconds if no connection

# AirVPN API URLs
airvpn_status_url = f"https://airvpn.org/api/status/?key={AIRVPN_API_KEY}&format=json"
airvpn_ip_check_url = f"https://airvpn.org/api/whatismyip/?key={AIRVPN_API_KEY}&format=json"
ipify_url = "https://api.ipify.org?format=json"
personal_ip = None  # This will be set to the initial IP detected before connecting to VPN

# Load the log file
def load_log():
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return json.load(f)
    return {}

# Save the log file
def save_log(log):
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=4)

# Load skip list from file
def load_skip_list():
    if os.path.exists(skip_list_file):
        with open(skip_list_file, 'r') as f:
            return json.load(f)
    return {}

# Save skip list to file
def save_skip_list(skip_list):
    with open(skip_list_file, 'w') as f:
        json.dump(skip_list, f, indent=4)

# Clear skip list if --clearskiplist flag is provided
def handle_flags(skip_list):
    if '--clearskiplist' in sys.argv:
        skip_list.clear()  # Clear the in-memory list
        save_skip_list(skip_list)  # Save cleared list to file
        print("Skip list cleared.")
        sys.exit(0)

# Function to check current IP using AirVPN API with ipify fallback
def get_current_ip():
    try:
        response = requests.get(airvpn_ip_check_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("airvpn") is True:
            return data.get("ip")
        else:
            raise ValueError("Not connected to AirVPN.")
    except (requests.RequestException, ValueError):
        try:
            response = requests.get(ipify_url, timeout=10)
            response.raise_for_status()
            return response.json().get("ip")
        except requests.RequestException as e:
            print(f"Error checking IP: {e}")
            return None

# Get server status using AirVPN API and check health
def get_server_status(server_name, skip_list):
    if server_name in skip_list:
        print(f"Skipping {server_name} due to {skip_list[server_name]}.")
        return None
    
    try:
        response = requests.get(airvpn_status_url)
        response.raise_for_status()
        status_data = response.json()

        for server in status_data.get("servers", []):
            if server.get("public_name") == server_name:
                reason = server.get("warning", "Unknown issue") if server.get("health") != "ok" else None
                if reason:
                    skip_list[server_name] = reason
                    save_skip_list(skip_list)  # Save after adding reason
                    return None
                return server
        print(f"Server '{server_name}' not found in status data.")
        return None

    except requests.RequestException as e:
        print(f"Error fetching server status: {e}")
        return None

# Connect to VPN and monitor Hummingbird logs for success
def connect_to_vpn(config_file, skip_list):
    server_name = config_file.split(".")[0]

    server_status = get_server_status(server_name, skip_list)
    if not server_status:
        return None

    command = f"sudo hummingbird {config_dir}/{config_file}"
    print(f"Connecting to VPN with {config_file}")

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    for line in process.stdout:
        if "EVENT: CONNECTED" in line:
            return process
        elif "AUTH_FAILED" in line or "EVENT: DISCONNECTED" in line:
            break

    process.terminate()
    process.wait()
    skip_list[server_name] = "connection failure"
    save_skip_list(skip_list)
    return None

# Disconnect VPN
def disconnect_vpn(process):
    if process:
        print("Disconnecting VPN...")
        process.terminate()
        process.wait()

# Click Dragon Village link
def click_dragon_village_link(link):
    try:
        response = requests.get(link)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Graceful shutdown handler
def graceful_exit(signal, frame):
    print("\nGraceful shutdown initiated...")
    global vpn_process
    if vpn_process:
        disconnect_vpn(vpn_process)  # Ensure VPN is disconnected
    save_log(log)
    save_skip_list(skip_list)
    print("Logs and skip list saved. Exiting program.")
    sys.exit(0)

# Main function
def main():
    global personal_ip, vpn_process, log, skip_list
    log = load_log()
    skip_list = load_skip_list()
    handle_flags(skip_list)

    # Set up signal handling for graceful exit
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)

    # Check initial IP and set it as personal IP
    personal_ip = get_current_ip()
    if personal_ip is None:
        print("Unable to fetch initial IP address. Exiting.")
        return

    # Get user input
    dragon_link = input("Enter the Dragon Village link: ")

    # Check if this link has been logged before and has non-zero views
    if dragon_link in log:
        current_views = log[dragon_link]["views_generated"]
        if current_views > 0:
            print(f"This link has already been given {current_views} views.")
        additional_views = int(input("How many additional views do you want? (Enter 0 to quit): "))
        if additional_views == 0:
            print("Program terminated.")
            return
    else:
        additional_views = int(input("Enter the number of views you want: "))
        if additional_views == 0:
            print("Program terminated.")
            return
        log[dragon_link] = {"used_ovpn_files": [], "views_generated": 0}
        current_views = 0

    # Set target views
    target_views = current_views + additional_views
    config_files = [f for f in os.listdir(config_dir) if f.endswith(".ovpn")]

    for config_file in config_files:
        # Skip this config if it was already used for the current link
        if config_file in log[dragon_link]["used_ovpn_files"]:
            continue

        if current_views >= target_views:
            print(f"Reached {target_views} views!")
            break

        vpn_process = connect_to_vpn(config_file, skip_list)
        if vpn_process:
            current_ip = get_current_ip()
            if current_ip and current_ip != personal_ip:
                print(f"Current IP: {current_ip}")
                if click_dragon_village_link(dragon_link):
                    current_views += 1
                    print(f"View successful! Total views: {current_views}")
                    log[dragon_link]["used_ovpn_files"].append(config_file)
                    log[dragon_link]["views_generated"] = current_views
                else:
                    print("Failed to register the view.")
            disconnect_vpn(vpn_process)

    save_log(log)
    print(f"Reached {current_views}/{target_views} views.")

if __name__ == "__main__":
    vpn_process = None
    main()