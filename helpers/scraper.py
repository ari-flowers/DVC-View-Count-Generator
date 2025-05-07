import requests
from bs4 import BeautifulSoup

def fetch_live_view_count(dragon_url):
    try:
        response = requests.get(dragon_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        view_span = soup.select_one("div.viewText span")
        if view_span:
            return int(view_span.text.strip())

        print("⚠️ View count element not found.")
        return None
    except Exception as e:
        print(f"⚠️ Failed to fetch live view count: {e}")
        return None