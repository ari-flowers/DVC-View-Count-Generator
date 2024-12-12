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

def verify_ovpn_files():
    server_names = fetch_server_names()
    mismatched_files = []  # Track files that do not match any server name

    # Iterate over each file in the config directory
    for filename in os.listdir(config_dir):
        if filename.endswith(".ovpn"):
            # Remove the '.ovpn' extension to get the server name
            file_server_name = filename.rsplit(".", 1)[0]

            # Check if this name exists in the fetched server names
            if file_server_name not in server_names:
                mismatched_files.append(filename)

    # Report any mismatched files
    if mismatched_files:
        print("\nThe following files do not match any known server names from the API:")
        for file in mismatched_files:
            print(f"- {file}")
    else:
        print("All .ovpn files match the server names from the API.")

# Run the verification function
verify_ovpn_files()