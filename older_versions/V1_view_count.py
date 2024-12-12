import os
import json
import requests
import subprocess
import time
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
AIRVPN_API_KEY = os.getenv("AIRVPN_API_KEY")

# Paths and file names
config_dir = "configs/"
log_file = "vpn_usage_log.json"
skip_list_file = "vpn_skip_list.txt"
MAX_RETRIES = 2
personal_ip = "97.126.112.187"
MAX_TIMEOUT = 10  # Timeout after x seconds if no connection

# AirVPN status and IP-check API URLs
airvpn_status_url = f"https://airvpn.org/api/status/?key={AIRVPN_API_KEY}&format=json"
airvpn_ip_check_url = f"https://airvpn.org/api/whatismyip/?key={AIRVPN_API_KEY}&format=json"

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

# Load skipped servers from file
def load_skip_list():
    if os.path.exists(skip_list_file):
        with open(skip_list_file, 'r') as f:
            return set(f.read().splitlines())
    return set()

# Save skipped servers to file
def save_skip_list(skip_list):
    with open(skip_list_file, 'w') as f:
        f.write("\n".join(skip_list))

# Function to check the current public IP address using AirVPN's whatismyip API
def get_current_ip():
    try:
        response = requests.get(airvpn_ip_check_url)
        response.raise_for_status()
        ip_info = response.json()

        # Ensure the IP is an AirVPN IP and not the personal IP
        if ip_info.get("airvpn") and ip_info.get("ip") != personal_ip:
            return ip_info.get("ip")
        else:
            print(f"Not connected to VPN or using personal IP: {ip_info.get('ip')}")
            return None
    except requests.RequestException as e:
        print(f"Error checking IP: {e}")
        return None

# Function to get server status using AirVPN API
def get_server_status(server_name):
    try:
        response = requests.get(airvpn_status_url)
        response.raise_for_status()
        status_data = response.json()

        for server in status_data.get("servers", []):
            if server.get("public_name") == server_name:
                if server.get("health") == "ok":
                    return server
                else:
                    # Log the specific reason for skipping
                    reason = server.get("warning", "Unspecified error")
                    print(f"Skipping {server_name} due to: {reason}")
                    return None
        print(f"Server '{server_name}' not found in status data.")
        return None
    except requests.RequestException as e:
        print(f"Error fetching server status: {e}")
        return None

# Function to ensure we're connected to a VPN by checking the IP
def ensure_vpn_connected():
    current_ip = get_current_ip()
    if not current_ip:
        print("VPN connection not detected, reconnecting...")
        return False
    else:
        print(f"VPN connected with IP: {current_ip}")
        return True

# Function to connect to a VPN with suppressed logs
def connect_to_vpn(config_file):
    server_name = config_file.split(".")[0]
    server_status = get_server_status(server_name)

    if not server_status:
        return None

    command = f"sudo hummingbird {config_dir}/{config_file}"
    print(f"Connecting to VPN with {config_file}")

    retry_count = 0
    while retry_count < MAX_RETRIES:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)  # Wait briefly to allow the VPN connection to establish

        if ensure_vpn_connected():
            return process  # VPN connected successfully

        print(f"Connection attempt {retry_count + 1} failed for {config_file}. Retrying...")
        retry_count += 1
        process.terminate()
        process.wait()

    print(f"Connection failed for {config_file} after {MAX_RETRIES} attempts.")
    return None

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

        if config_file in log[dragon_link]["used_ovpn_files"] or config_file in skip_list:
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
                    save_log(log)
                else:
                    print("Failed to register the view.")
            disconnect_vpn(vpn_process)
        else:
            print(f"Failed to connect with {config_file}. Adding to skip list.")
            skip_list.add(config_file)
            save_skip_list(skip_list)
            time.sleep(3)

    print(f"Reached {current_views}/{target_views} views.")
    save_log(log)

if __name__ == "__main__":
    main()