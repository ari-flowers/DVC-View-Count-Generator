# 🐉 CrackedUp View Count Script

This script automates VPN rotation to increase views on Dragon Village Collection (DVC) eggs or hatchlings using AirVPN. It ensures views are only counted once per IP, logs which servers have been used, and supports live view scraping and personality-based targeting.

---

## 🚀 Features

- ✅ **Live view count scraping** from DVC share links
- ✅ **Personality goal targeting** (e.g., Silent, Lovely, Arrogant)
- ✅ **Rainbow spinner** while connecting to VPN
- ✅ **AirVPN server health checks** via official API
- ✅ **SQLite database logging** for clicks and skipped servers
- ✅ **Skips unhealthy or failed VPN servers**
- ✅ **Graceful shutdown** with automatic `sudo hummingbird --recover-network`

---

## 📦 Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Minimal `requirements.txt`:

```
requests
beautifulsoup4
python-dotenv
pandas
tabulate
```

---

## 🛠 Setup

1. Clone the repo and enter the directory
2. Place your `.ovpn` config files into the `configs/` folder
3. Create a `.env` file in the project root with:

```env
AIRVPN_API_KEY=your_api_key_here
```

4. Run the DB initializer:

```bash
python db/init_db.py
python db/sync_servers.py
```

(Optional: `python db/migrations/add_personality_fields.py` if needed)

---

## 🧪 Usage

```bash
python view_count.py
```

You’ll be prompted to:

- Enter a DVC share link (e.g. https://dragon.dvc.land/view/us?id=...)
- Choose a personality (e.g. `cute`, `lovely`, `silent`) or manually enter a view target
- Watch the rainbow spinner work its magic 🌈

The script will:

- Rotate through working AirVPN servers
- Skip unhealthy or previously used ones
- Stop when the desired number of views is reached

---

## 🔍 CLI Tools

```bash
python db/browse_db.py
```

- View logs, skipped servers, and click history

More CLI tools coming soon!

---

## 🎯 Supported Personalities

These personalities are view-based:

| Personality   | View Requirement | Notes |
|---------------|------------------|-------|
| Silent        | Exactly 0        | |
| Solitary      | Exactly 1        | |
| Reserved      | 5–9              | |
| Mischievous   | 50–99            | |
| Lousy         | 95–99            | |
| Friendly      | 100+             | Requires set as partner + village visits |
| Extroverted   | 100+             | Partner activity required |
| Cute          | Exactly 199      | Nickname, 99 EV total, no STR, incubator |
| Lovely        | 200+             | |
| Arrogant      | 200+             | Requires all EVs ≥ 25 |

*Your script adjusts view counts accordingly and will stop when the target is reached.*

---

## ❤️ Credits

Created by Ari Flowers — view automation for cute digital dragons 🐉  
Supports AirVPN + Dragon Village Collection

---

## 📜 License

MIT License