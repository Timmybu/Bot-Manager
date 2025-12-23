
import subprocess
import threading
import time
import os
import psutil
from datetime import datetime

# --- CONFIGURATION ---
PRISM_EXECUTABLE = "C:/Users/Timmyb/AppData/Local/Programs/PrismLauncher/prismlauncher.exe"  # Ensure this is in your PATH or use full path

INVALID_SESSION_ERROR = "Failed to login: Invalid session"

# How many seconds to wait after launching a game before checking/launching the next one
LAUNCH_DELAY = 20

# List your instances and the server they should join
INSTANCES = [
    {
        "name": "Alt1",       # Prism Instance Name
        "server": "play.donutsmp.net", # Server IP
        "account": "00zb" # <--- EXACT Name from Prism Accounts list
    },
    {
        "name": "Alt2",
        "server": "play.donutsmp.net",
        "account": "ChingChing13"
    },
    {
        "name": "Alt3",       # Prism Instance Name
        "server": "play.donutsmp.net", # Server IP
        "account": "BobBild12" # <--- EXACT Name from Prism Accounts list
    },
    {
        "name": "Alt4",
        "server": "play.donutsmp.net",
        "account": "BongBongLong"
    }
]
HEARTBEAT_TIMEOUT = 60  # Seconds before considering the instance frozen

def get_heartbeat_file(instance_name):
    # This file should be written by your Glazed addon inside the instance folder
    # Adjust path to match where your instance saves files
    base_path =  f"C:/Users/Timmyb/AppData/Roaming/PrismLauncher/instances/{instance_name}/minecraft/heartbeat.txt"
    return os.path.join(base_path, "heartbeat.txt")

def is_instance_running(process):
    if process is None:
        return False
    
    # .poll() returns None if the process is still running.
    # It returns an exit code (like 0 or 1) if it has finished/crashed.
    return process.poll() is None

def launch_instance(instance):
    print(f"[{datetime.now()}] Launching {instance['name']} with account {instance['account']}...")
    
    # Base command: Launch instance (-l) and auto-join server (-s)
    cmd = [PRISM_EXECUTABLE, "-l", instance['name'], "-s", instance['server']]
    
    # ADDED: If an account is specified, add the -a flag
    if "account" in instance:
        cmd.extend(["-a", instance['account']])
    
    # redirects stdout so we can read it (remains the same as before)
    proc = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True, 
        encoding='utf-8',
        errors='ignore'
    )

    # Start a background thread to read the logs for this specific process
    log_thread = threading.Thread(target=monitor_logs, args=(proc, instance['name']))
    log_thread.daemon = True # Ensures thread dies if main script dies
    log_thread.start()

    return proc

def monitor_logs(proc, instance_name):
    """
    Reads the game's output line by line. 
    If it sees the error, it kills the process.
    """
    try:
        # Read line by line until the process ends
        for line in proc.stdout:
            line = line.strip()
            if not line: continue
            
            # Optional: Print game output to your meta-console
            # print(f"[{instance_name}] {line}")

            if INVALID_SESSION_ERROR in line:
                print(f"[{datetime.now()}] [{instance_name}] DETECTED INVALID SESSION! Killing process...")
                proc.kill() # Kill the game immediately
                break # Stop reading logs for this dead process
                
    except Exception as e:
        print(f"[{instance_name}] Log monitor error: {e}")


def monitor_loop():
    running_instances = {}  # Map instance name to process object

    while True:
        # We iterate through the list of instances you configured
        for config in INSTANCES:
            name = config['name']
            
            # 1. Check if process is alive
            if name not in running_instances or not is_instance_running(running_instances[name]):
                print(f"[{name}] Not running or crashed. Restarting...")
                
                # Launch the game
                running_instances[name] = launch_instance(config)
                
                # --- THE FIX ---
                # Wait here so the computer has time to load the game files 
                # before we try to start the next one.
                print(f"Waiting {LAUNCH_DELAY} seconds for {name} to initialize...")
                time.sleep(LAUNCH_DELAY)
                
                continue # Skip the rest of the loop for this instance

            # 2. Check Heartbeat (Freeze Detection) - Optional
            heartbeat_path = get_heartbeat_file(name)
            if os.path.exists(heartbeat_path):
                last_modified = os.path.getmtime(heartbeat_path)
                if time.time() - last_modified > HEARTBEAT_TIMEOUT:
                    print(f"[{name}] FROZEN detected (Heartbeat old). Killing and restarting...")
                    try:
                        running_instances[name].kill()
                    except:
                        pass
                    running_instances[name] = launch_instance(config)
                    
                    # Also wait after a restart to prevent spamming
                    time.sleep(LAUNCH_DELAY)

        time.sleep(10) # Check every 10 seconds

if __name__ == "__main__":
    monitor_loop()