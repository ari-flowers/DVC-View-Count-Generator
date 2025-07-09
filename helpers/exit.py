import signal
import subprocess
import sys

vpn_process = None  # Will be set externally

def set_vpn_process(proc):
    global vpn_process
    vpn_process = proc

def graceful_exit(sig, frame):
    print("\n Graceful shutdown initiated...")
    if vpn_process:
        try:
            print("🔌 Terminating VPN...")
            vpn_process.terminate()
            vpn_process.wait()
        except Exception:
            pass
        print("🔄 Recovering network...")
        subprocess.run("sudo hummingbird --recover-network", shell=True)
    print("👋 Exiting program. Have a great day :)")
    sys.exit(0)

def setup_signals():
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)