# Last stable version that works until it hits a server with an error and is unable to connect. Adding skip list functionality in future versions.

import os
import json
import requests
import subprocess

# Path to the VPN config files directory
config_dir = "configs/"
log_file = "vpn_usage_log.json"
ip_check_url = "https://api.ipify.org"
MAX_RETRIES = 2
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

# Function to check the current public IP address
def get_current_ip():
    try:
        response = requests.get(ip_check_url, timeout=10)
        return response.text if response.status_code == 200 else None
    except requests.RequestException as e:
        print(f"Error checking IP: {e}")
        return None

# Function to ensure we're connected to a VPN, not the personal IP
def ensure_vpn_connected():
    current_ip = get_current_ip()
    if current_ip == personal_ip:
        print(f"Not connected to VPN (current IP: {current_ip}), reconnecting...")
        return False
    else:
        print(f"VPN connected with IP: {current_ip}")
        return True

# Function to connect to a VPN
def connect_to_vpn(config_file):
    command = f"sudo hummingbird {config_dir}/{config_file}"
    print(f"Connecting to VPN with {config_file}")
    
    retry_count = 0
    process = None
    while retry_count < MAX_RETRIES:
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while True:
                output = process.stdout.readline()
                if "EVENT: CONNECTED" in output:
                    return process  # VPN is connected
        except subprocess.TimeoutExpired:
            retry_count += 1
            print(f"Connection attempt {retry_count} failed for {config_file}. Retrying...")
    
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
            continue  # Skip this file if it's already been used for this link

        vpn_process = connect_to_vpn(config_file)
        if vpn_process:
            if ensure_vpn_connected():
                current_ip = get_current_ip()
                if current_ip:
                    print(f"Current IP: {current_ip}")
                    if click_dragon_village_link(dragon_link):
                        current_views += 1
                        print(f"View successful! Total views: {current_views}")
                        log[dragon_link]["used_ovpn_files"].append(config_file)
                        log[dragon_link]["views_generated"] = current_views
                        save_log(log)
                    else:
                        print("Failed to register the view.")
            else:
                print("Failed to get current IP.")
            disconnect_vpn(vpn_process)
        else:
            print(f"Failed to connect with {config_file}")

    print(f"Reached {current_views}/{target_views} views.")
    save_log(log)

if __name__ == "__main__":
    main()