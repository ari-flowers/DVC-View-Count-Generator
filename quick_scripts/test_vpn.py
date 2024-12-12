import requests

# Function to check the current IP
def check_current_ip():
    try:
        response = requests.get('https://api.ipify.org')
        if response.status_code == 200:
            return response.text
        else:
            print("Failed to retrieve IP")
            return None
    except Exception as e:
        print(f"Error checking IP: {e}")
        return None

# Function to ensure you are connected to a VPN
def ensure_vpn_connected(personal_ip):
    current_ip = check_current_ip()
    if current_ip == personal_ip:
        print(f"Not connected to VPN (current IP: {current_ip}), reconnecting...")
        return False
    else:
        print(f"Connected to VPN with IP: {current_ip}")
        return True

# Function to click the Dragon Village link
def click_dragon_village_link(link, personal_ip):
    if ensure_vpn_connected(personal_ip):
        try:
            response = requests.get(link)
            if response.status_code == 200:
                print("Click successful!")
            else:
                print("Failed to click the link")
        except Exception as e:
            print(f"Error clicking the link: {e}")
    else:
        print("VPN not connected, skipping click.")

# Replace with your actual personal IP
personal_ip = "97.126.112.187"

# Example usage
dragon_village_link = "https://dragon.dvc.land/view/us?id=6713dd6189c3e82fa17f27bd"
click_dragon_village_link(dragon_village_link, personal_ip)