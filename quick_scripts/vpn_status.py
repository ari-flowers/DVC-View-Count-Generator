import requests
import os

def fetch_server_names():
    api_key = os.getenv("AIRVPN_API_KEY")  # Make sure your .env file has AIRVPN_API_KEY set correctly
    url = f"https://airvpn.org/api/status/?key={api_key}&format=json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        status_data = response.json()
        
        # Extract server names
        server_names = [server.get("public_name") for server in status_data.get("servers", [])]
        
        # Print server names and count
        print("Server names from AirVPN API:")
        for name in server_names:
            print(name)
        print(f"\nTotal number of servers returned: {len(server_names)}")

        return server_names

    except requests.exceptions.RequestException as e:
        print(f"Error fetching server names: {e}")
        return []

# Call the function
fetch_server_names()