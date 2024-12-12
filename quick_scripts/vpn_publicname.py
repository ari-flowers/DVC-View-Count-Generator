import os
import requests

# Load API key from environment
api_key = os.getenv("AIRVPN_API_KEY")
config_dir = "configs/"

def fetch_server_names():
    url = f"https://airvpn.org/api/status/?key={api_key}&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        status_data = response.json()
        
        # Extract server names from the status data
        server_names = {server["public_name"] for server in status_data.get("servers", [])}
        return server_names

    except requests.exceptions.RequestException as e:
        print(f"Error fetching server names: {e}")
        return set()

def rename_ovpn_files():
    server_names = fetch_server_names()
    unmatched_files = []  # To track files that don't match any server name

    # Iterate over each file in the config directory
    for filename in os.listdir(config_dir):
        if filename.endswith(".ovpn"):
            # Extract the server name by splitting on underscores and taking the last relevant part
            server_name_part = filename.split("_")[2]  # Assumes consistent filename format
            
            if server_name_part in server_names:
                new_filename = f"{server_name_part}.ovpn"
                full_path = os.path.join(config_dir, filename)
                new_path = os.path.join(config_dir, new_filename)
                
                os.rename(full_path, new_path)
                print(f"Renamed {filename} to {new_filename}")
            else:
                unmatched_files.append(filename)

    # Print unmatched files for further investigation
    if unmatched_files:
        print("\nThe following files did not match any known server names:")
        for file in unmatched_files:
            print(f"- {file}")

# Run the renaming function
rename_ovpn_files()