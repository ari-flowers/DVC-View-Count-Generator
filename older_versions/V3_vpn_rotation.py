import os
import json
import requests
import subprocess
import time
import sys

# Paths and file names
config_dir = "configs/"
log_file = "vpn_usage_log.json"
skip_list_file = "vpn_skip_list.txt"
ip_check_url = "https://api.ipify.org"
MAX_RETRIES = 2
personal_ip = "97.126.112.187"
MAX_TIMEOUT = 20  # Timeout after 20 seconds if no connection

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
            start_time = time.time()
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Read the logs to detect issues or successful connection
            while True:
                output = process.stdout.readline().strip()
                if not output and time.time() - start_time > MAX_TIMEOUT:
                    raise subprocess.TimeoutExpired(cmd=command, timeout=MAX_TIMEOUT)

                if "EVENT: CONNECTED" in output:
                    return process  # VPN connected

                if "AUTH_FAILED" in output:
                    raise RuntimeError(f"AUTH_FAILED for {config_file}")

        except subprocess.TimeoutExpired:
            retry_count += 1
            print(f"Connection attempt {retry_count} timed out for {config_file}. Retrying...")
        except RuntimeError as e:
            print(e)
            return None

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

# Function to handle showing or clearing the skip list
def handle_flags():
    if '--showskiplist' in sys.argv:
        skip_list = load_skip_list()
        print("\nSkipped servers:")
        if skip_list:
            for server in skip_list:
                print(f"- {server}")
        else:
            print("No servers in the skip list.")
        sys.exit(0)
    
    if '--clearskiplist' in sys.argv:
        save_skip_list(set())  # Clear the skip list by saving an empty set
        print("Skip list cleared.")
        sys.exit(0)

    if '--clearvpnlog' in sys.argv:
        save_log({})  # Clear the VPN usage log by saving an empty dictionary
        print("VPN usage log cleared.")
        sys.exit(0)

# Main function
def main():
    handle_flags()

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

        if config_file in log[dragon_link]["used_ovpn_files"]:
            continue  # Skip this file if it's already been used for this link

        if config_file in skip_list:
            print(f"Skipping {config_file} (listed in skip list).")
            continue

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
            print(f"Failed to connect with {config_file}. Adding to skip list.")
            skip_list.add(config_file)
            save_skip_list(skip_list)
            time.sleep(3)  # Add a delay after adding to the skip list

    print(f"Reached {current_views}/{target_views} views.")
    save_log(log)

if __name__ == "__main__":
    main()