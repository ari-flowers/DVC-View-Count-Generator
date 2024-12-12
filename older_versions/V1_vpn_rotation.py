# Original VPN rotation logic with run time logs, before implementing Dragon Village logic. 

import os
import requests
import time
import subprocess

# Path to the VPN config files directory
config_dir = "configs/"

# List all .ovpn files in the config directory
config_files = [f for f in os.listdir(config_dir) if f.endswith(".ovpn")]

# Store unique IPs, failed servers, and connection times
unique_ips = set()
failed_servers = []
connection_times = []  # Store the time it takes for each connection
MAX_IPS = 10  # Set lower for testing
ip_check_url = "https://api.ipify.org"  # API to check current public IP
MAX_RETRIES = 2  # Retry up to 2 times for each server

def get_current_ip():
    """Fetch the current public IP address."""
    try:
        response = requests.get(ip_check_url, timeout=10)
        return response.text if response.status_code == 200 else None
    except requests.RequestException as e:
        print(f"Error checking IP: {e}")
        return None

def connect_to_vpn(config_file):
    """Connect to a VPN server using the Hummingbird client and wait for connection."""
    command = f"sudo hummingbird {config_dir}/{config_file}"
    print(f"Connecting to VPN with {config_file}")
    
    retry_count = 0
    process = None
    while retry_count < MAX_RETRIES:
        try:
            start_time = time.time()
            # Capture the logs from Hummingbird using Popen, suppress the logs
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Continuously read the output to check for the EVENT: CONNECTED message
            while True:
                output = process.stdout.readline()
                if output:
                    if "EVENT: CONNECTED" in output:
                        break  # VPN is connected

            end_time = time.time()
            connection_time = end_time - start_time
            connection_times.append((config_file, connection_time))  # Log time for this server
            return process  # Return the process so we can terminate it later
        except subprocess.TimeoutExpired:
            retry_count += 1
            print(f"Connection attempt {retry_count} failed for {config_file}. Retrying...")
            time.sleep(5)  # Short delay before retrying
    
    print(f"Connection failed for {config_file} after {MAX_RETRIES} attempts.")
    failed_servers.append(config_file)
    if process:
        process.terminate()  # Terminate if there's any hanging process
    return None  # Connection failed after retries

def disconnect_vpn(process):
    """Disconnect from the VPN by gracefully terminating the Hummingbird process."""
    if process:
        print("Disconnecting VPN...")
        process.terminate()  # Gracefully stop the process, like Ctrl + C
        process.wait()  # Wait for the process to finish termination
        # Removed the time.sleep(5) here

def main():
    start_time = time.time()  # Start the timer for the entire program

    for config_file in config_files:
        if len(unique_ips) >= MAX_IPS:
            print(f"Reached {MAX_IPS} unique IPs!")
            break
        
        vpn_process = connect_to_vpn(config_file)
        
        if vpn_process:
            print("Connected to VPN. Now checking IP...")
            current_ip = get_current_ip()
            if current_ip:
                print(f"Current IP: {current_ip}")
                if current_ip not in unique_ips:
                    print(f"New unique IP: {current_ip}")
                    unique_ips.add(current_ip)
                else:
                    print("IP already used, moving to the next server.")
            else:
                print("Failed to retrieve current IP.")
            
            disconnect_vpn(vpn_process)
        
        # Log connection time and unique IP count after each connection
        print(f"Connection time: {connection_times[-1][1]:.2f} seconds")
        print(f"Current unique IP count: {len(unique_ips)}/{MAX_IPS}")

    # Log failed servers if there are any
    if failed_servers:
        print(f"\nServers that failed to connect: {len(failed_servers)}")
        for server in failed_servers:
            print(f"- {server}")

    # Print connection times for each server
    print("\nConnection times for each server:")
    for server, time_taken in connection_times:
        print(f"- {server}: {time_taken:.2f} seconds")

    # Calculate and print total runtime
    total_runtime = time.time() - start_time
    print(f"\nTotal program runtime: {total_runtime:.2f} seconds")

    print(f"\nTotal unique IPs collected: {len(unique_ips)}")
    print("Done!")

if __name__ == "__main__":
    main()