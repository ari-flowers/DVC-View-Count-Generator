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
python view_count.py [options]
```

---

### ⚙️ Command-Line Flags

| Flag              | Type     | Description                                                  |
|-------------------|----------|--------------------------------------------------------------|
| `--link`          | `str`    | The DVC dragon share link to automate views for             |
| `--personality`   | `str`    | Target a specific personality (e.g. `cute`, `lovely`, `sil`)|
| `--views`         | `int`    | Manually override total view target (bypasses personality)  |
| `--limit`         | `int`    | Maximum number of views to add during this run              |
| `--dry-run`       | flag     | Simulate the run without making real HTTP requests          |

---

### 🧠 Examples

#### 🎯 Target a personality with automatic view goal:
```bash
python view_count.py --link https://dragon.dvc.land/view/us?id=abc123 --personality cute
```

#### 🔢 Manually request 50 views:
```bash
python view_count.py --link https://dragon.dvc.land/view/us?id=abc123 --views 50
```

#### 🧪 Test safely without clicking:
```bash
python view_count.py --link https://dragon.dvc.land/view/us?id=abc123 --views 20 --dry-run
```

#### 🔐 Limit to 3 views this run:
```bash
python view_count.py --link https://dragon.dvc.land/view/us?id=abc123 --personality lovely --limit 3
```

---

You can still run the script without flags and it will guide you interactively.

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
| Solitary      | Exactly 1        | Views === 1, all EVs end with 1 |
| Reserved      | 5–9              | Views = 5-9, incubator |
| Mischievous   | 50–99            | Each EV is different and ends with 9, no sickness |
| Lousy         | 95–99            | Views = 95-99 |
| Friendly      | 100+             | Views ≥ 100, nickname, cares "Good!" or higher |
| Extroverted   | 100+             | Views ≥ 100, set as partner and visit 30+ villages |
| Cute          | Exactly 199      | Nickname, 99 EV total, no STR, incubator, no sickness |
| Lovely        | 300+             | Views ≥ 300|
| Arrogant      | 200+             | Requires all EVs ≥ 25 |

*The script adjusts view counts accordingly and will stop when the target is reached.*

---

## ❤️ Credits

Created by Ari Flowers — view automation for cute digital dragons 🐉  
Supports AirVPN + Dragon Village Collection

---

## 📜 License

MIT License