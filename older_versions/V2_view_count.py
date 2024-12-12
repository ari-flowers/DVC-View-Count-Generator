import os
import json
import requests
import subprocess
import time
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
AIRVPN_API_KEY = os.getenv("AIRVPN_API_KEY")

# Paths and file names
config_dir = "configs/"
log_file = "vpn_usage_log.json"
skip_list_file = "vpn_skip_list.json"
MAX_TIMEOUT = 10  # Timeout after x seconds if no connection

# AirVPN status and IP check API URLs
airvpn_status_url = f"https://airvpn.org/api/status/?key={AIRVPN_API_KEY}&format=json"
airvpn_ip_check_url = f"https://airvpn.org/api/whatismyip/?key={AIRVPN_API_KEY}&format=json"
backup_ip_check_url = "https://api.ipify.org?format=json"
personal_ip = "97.126.112.187"

# Function to load the log file
def load_log():
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return json.load(f)
    return {}

# Function to save the log file
def save_log(log):
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=4)

# Load skipped servers with reasons from file
def load_skip_list():
    if os.path.exists(skip_list_file):
        with open(skip_list_file, 'r') as f:
            return json.load(f)
    return {}

# Save skipped servers with reasons to file
def save_skip_list(skip_list):
    with open(skip_list_file, 'w') as f:
        json.dump(skip_list, f, indent=4)

# Function to check the current IP address with AirVPN or fallback to ipify
def get_current_ip():
    try:
        response = requests.get(airvpn_ip_check_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data["result"] == "ok":
            return data["ip"]
    except requests.RequestException:
        print("AirVPN IP check failed, falling back to ipify.")
        try:
            response = requests.get(backup_ip_check_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data["ip"]
        except requests.RequestException as e:
            print(f"Error checking IP: {e}")
            return None

# Function to get server status with caching
server_status_cache = {}

def get_server_status(server_name):
    if server_name in server_status_cache:
        return server_status_cache[server_name]

    try:
        response = requests.get(airvpn_status_url)
        response.raise_for_status()
        status_data = response.json()

        # Cache the status of each server to avoid repeat API calls
        for server in status_data.get("servers", []):
            public_name = server.get("public_name")
            server_status_cache[public_name] = server

            if public_name == server_name:
                if server.get("health") == "ok":
                    return server
                elif server.get("health") == "error" or "maintenance" in server.get("warning", "").lower():
                    skip_list[server_name] = server.get("warning", "error or maintenance")
                    print(f"Skipping {server_name} due to {skip_list[server_name]}.")
                    return None

        print(f"Server '{server_name}' not found in status data.")
        skip_list[server_name] = "not found in status data"
        return None

    except requests.RequestException as e:
        print(f"Error fetching server status: {e}")
        return None

# Function to connect to a VPN without fixed sleep
def connect_to_vpn(config_file):
    server_name = config_file.split(".")[0]
    
    # Check skip list before calling the API
    if server_name in skip_list:
        print(f"Skipping {server_name} due to {skip_list[server_name]}.")
        return None

    server_status = get_server_status(server_name)
    if not server_status:
        return None

    command = f"sudo hummingbird {config_dir}/{config_file}"
    print(f"Connecting to VPN with {config_file}")

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Actively monitor for connection by checking IP availability
    start_time = time.time()
    while time.time() - start_time < MAX_TIMEOUT:
        if ensure_vpn_connected():
            return process  # VPN connected successfully
        time.sleep(1)  # Brief wait before the next check

    process.terminate()
    process.wait()
    print(f"Failed to connect with {config_file}. Adding to skip list.")
    skip_list[server_name] = "connection failure"
    return None

# Function to ensure VPN connection by checking the IP
def ensure_vpn_connected():
    current_ip = get_current_ip()
    if current_ip == personal_ip or current_ip is None:
        print(f"Not connected to VPN (current IP: {current_ip}), reconnecting...")
        return False
    else:
        print(f"VPN connected with IP: {current_ip}")
        return True

# Function to disconnect from a VPN
def disconnect_vpn(process):
    if process:
        print("Disconnecting VPN...")
        process.terminate()
        process.wait()

# Function to click the Dragon Village link
def click_dragon_village_link(link):
    try:
        response = requests.get(link)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Main function
def main():
    log = load_log()
    global skip_list
    skip_list = load_skip_list()

    # Get user input
    dragon_link = input("Enter the Dragon Village link: ")

    # Check if this link has been logged before
    if dragon_link in log:
        current_views = log[dragon_link]["views_generated"]
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

    # List all .ovpn files
    config_files = [f for f in os.listdir(config_dir) if f.endswith(".ovpn")]

    for config_file in config_files:
        if current_views >= target_views:
            print(f"Reached {target_views} views!")
            break

        if config_file in log[dragon_link]["used_ovpn_files"]:
            continue

        vpn_process = connect_to_vpn(config_file)
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
        else:
            print(f"Failed to connect with {config_file}. Adding to skip list.")
            time.sleep(3)

    print(f"Reached {current_views}/{target_views} views.")
    save_log(log)
    save_skip_list(skip_list)

if __name__ == "__main__":
    main()