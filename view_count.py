from helpers.scraper import fetch_live_view_count
from helpers.personality import PERSONALITY_VIEW_TARGETS, resolve_personality_goal
from helpers.vpn import (
    get_current_ip,
    server_is_healthy,
    connect_to_vpn,
    disconnect_vpn,
    extract_server_name,
)
import os
import requests
import subprocess
import sys
import time
import signal
import threading
import argparse
from datetime import datetime
from dotenv import load_dotenv
from db.db import (
    get_usable_servers,
    mark_server_skipped,
    log_click,
    upsert_server,
    get_used_servers_for_link,
    get_view_count_for_link,
    get_dragon_link_data,
    upsert_dragon_link,
)

# Load environment variables
load_dotenv()

# Global for graceful shutdown
personal_ip = None
vpn_process = None

# Graceful Exit Handling
def graceful_exit(sig, frame):
    print("\n Graceful shutdown initiated...")
    if vpn_process:
        disconnect_vpn(vpn_process)
        print("🔄 Recovering network...")
        subprocess.run("sudo hummingbird --recover-network", shell=True)
    print("👋 Exiting program. Have a great day :)")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

# Register Views via VPN Servers
def click_dragon_village_link(link):
    try:
        response = requests.get(link)
        return response.status_code == 200
    except requests.RequestException:
        return False

def rotate_vpns(dragon_link, target_views, live_views, args):
    global vpn_process
    current_views = 0
    remaining_views = target_views - live_views

    used_servers = get_used_servers_for_link(dragon_link)
    usable_servers = set(get_usable_servers())
    config_files = get_config_files(usable_servers)

    for config_file in config_files:
        server_name = extract_server_name(config_file)
        print(f"\U0001F50D Checking config: {config_file} → Server: {server_name}")

        if server_name in used_servers or current_views >= remaining_views:
            continue

        if attempt_view_with_server(dragon_link, server_name, config_file, args):
            current_views += 1
            used_servers.add(server_name)
            print(f"👀 Views: {live_views + current_views}/{target_views}")

    if current_views < remaining_views:
        print("\n⚠️ Reached the end of available VPN servers before hitting the full target.")
        print(f"📈 Views added: {current_views} / {remaining_views}")
        print("💡 Consider using in-game tools like Sea Creature Calling or View Count Amulets to reach the goal.")

    return current_views


def get_config_files(usable_servers):
    return [
        f for f in os.listdir("configs/")
        if f.endswith(".ovpn") and extract_server_name(f) in usable_servers
    ]


def attempt_view_with_server(dragon_link, server_name, config_file, args):
    global vpn_process
    vpn_process = connect_to_vpn(config_file)

    if not vpn_process:
        return False

    current_ip = get_current_ip()
    if not current_ip or current_ip == personal_ip:
        disconnect_vpn(vpn_process)
        return False

    print(f"🌐 VPN IP: {current_ip}")

    if args.dry_run:
        print(f"🔎 [Dry Run] Skipping click for {dragon_link} via {server_name}")
        log_click(dragon_link, server_name, success=False)
        disconnect_vpn(vpn_process)
        return False

    success = click_dragon_village_link(dragon_link)
    log_click(dragon_link, server_name, success=success)
    disconnect_vpn(vpn_process)

    if not success:
        print(f"❌ View failed via {server_name}")
        return False

    return True

# Summary Output
def print_summary(link, personality, target, start_views, added, start_time, end_time, dry_run):
    final = start_views + added
    runtime = int(end_time - start_time)
    print("\n📊 Summary")
    print(f"🔗 Link: {link}")
    if personality:
        print(f"🎯 Personality targeted: {personality}")
        if personality == "Lovely":
            print(f"🐠 In-game view count bonus used: {'Yes' if target == 200 else 'No'}")
    print(f"📈 Views added this run: {added}")
    print(f"👀 Final view count: {final}")
    print(f"🕒 Runtime: {runtime // 60}m {runtime % 60}s")
    if dry_run:
        print("⚠️ Dry run: no views were actually submitted.")

# Argparse CLI
def parse_args():
    parser = argparse.ArgumentParser(description="CrackedUp DVC View Automation Script")
    parser.add_argument("--link", type=str, help="Dragon Village share link")
    parser.add_argument("--personality", type=str, help="Target personality (e.g. cute, lovely, friendly)")
    parser.add_argument("--views", type=int, help="Override number of total views")
    parser.add_argument("--limit", type=int, help="Max views to add this run")
    parser.add_argument("--dry-run", action="store_true", help="Simulate run without clicking")
    return parser.parse_args()

# Main

def main(args):
    global personal_ip, vpn_process
    start_time = time.time()

    personal_ip = get_current_ip()
    if not personal_ip:
        print("❌ Could not determine your personal IP. Exiting.")
        return

    dragon_link = args.link or input("Enter the Dragon Village link: ").strip()
    link_data = get_dragon_link_data(dragon_link)
    stored_personality = link_data["personality_goal"] if link_data else None
    stored_target_views = link_data["target_views"] if link_data else None

    live_views = fetch_live_view_count(dragon_link)
    if live_views is None:
        print("❌ Could not retrieve view count from page. Exiting.")
        return
    print(f"🔍 Live view count on page: {live_views}")

    existing_views = get_view_count_for_link(dragon_link)
    if existing_views > 0:
        print(f"🧮 Views previously added: {existing_views}")

    personality_goal = None
    target_views = None

    if stored_personality and stored_target_views:
        print(f"🧠 This link previously targeted '{stored_personality}' with goal of {stored_target_views} views.")
        choice = input("💬 Use this setup again? (K = Keep, C = Change, M = Manual) ").strip().lower()
        if choice == "k":
            personality_goal = stored_personality
            target_views = stored_target_views
        elif choice == "c":
            personality_input = input("🧠 Enter new personality: ").strip()
            personality_goal, target_views = resolve_personality_goal(personality_input)
            if not personality_goal:
                return
        else:
            try:
                target_views = int(input("Enter the number of total views you want: "))
            except ValueError:
                print("❌ Invalid input.")
                return

        if personality_goal:
            upsert_dragon_link(dragon_link, personality_goal, target_views)
        views_added = rotate_vpns(dragon_link, target_views, live_views, args)
        end_time = time.time()
        print_summary(dragon_link, personality_goal, target_views, live_views, views_added, start_time, end_time, args.dry_run)
        return

    # No stored data, use CLI flags or prompt
    if args.personality:
        personality_goal, target_views = resolve_personality_goal(args.personality)
        if not personality_goal:
            return
        print(f"🎯 Targeting personality '{personality_goal}' requires {target_views} total views.")
    elif args.views is not None:
        target_views = args.views
    else:
        personality_input = input("💬 Which personality are you targeting? (or press Enter to input views manually) ").strip()
        if personality_input:
            personality_goal, target_views = resolve_personality_goal(personality_input)
            if not personality_goal:
                return
            print(f"🎯 Targeting personality '{personality_goal}' requires {target_views} total views.")
        else:
            try:
                target_views = int(input("Enter the number of total views you want: "))
            except ValueError:
                print("❌ Invalid input.")
                return

    if personality_goal:
        upsert_dragon_link(dragon_link, personality_goal, target_views)

    if args.limit:
        target_views = min(live_views + args.limit, target_views)
        print(f"⚠️ Applying --limit: Will only attempt to reach {target_views} total views this run.")

    if target_views <= live_views:
        print(f"✅ Already has {live_views}/{target_views} views. No additional views needed.")
        return

    views_added = rotate_vpns(dragon_link, target_views, live_views, args)
    end_time = time.time()
    print_summary(dragon_link, personality_goal, target_views, live_views, views_added, start_time, end_time, args.dry_run)

if __name__ == "__main__":
    args = parse_args()
    main(args)
