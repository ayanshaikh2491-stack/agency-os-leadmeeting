"""Start Playwright Chromium with CDP for SBA ChromeTool."""
import subprocess
import sys
import os
import signal
import time
import socket

CHROME = r"C:\Users\TAUSHEF\AppData\Local\ms-playwright\chromium-1228\chrome-win64\chrome.exe"
CDP_PORT = 9222
USER_DATA = os.path.expanduser(r"~\.chrome-sba-profile")

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def start_chrome():
    if is_port_open(CDP_PORT):
        print(f"Chrome already running on port {CDP_PORT}")
        return True

    os.makedirs(USER_DATA, exist_ok=True)

    args = [
        CHROME,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--disable-sync",
        f"--user-data-dir={USER_DATA}",
        "--window-size=1920,1080",
        "--no-first-run",
        "--disable-background-networking",
        "--disable-default-apps",
        "--mute-audio",
        "--disable-features=TranslateUI",
        "about:blank",
    ]

    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        print(f"Chrome started (PID: {proc.pid}) on port {CDP_PORT}")

        # Wait for it to be ready
        for i in range(30):
            if is_port_open(CDP_PORT):
                print(f"Chrome ready after {i+1}s")
                # Save PID
                import json
                pid_file = os.path.expanduser("~/.sba_chrome_pid")
                with open(pid_file, "w") as f:
                    json.dump({"pid": proc.pid, "port": CDP_PORT}, f)
                return True
            time.sleep(1)

        print("Timeout waiting for Chrome to start")
        return False
    except Exception as e:
        print(f"Failed to start Chrome: {e}")
        return False

def stop_chrome():
    pid_file = os.path.expanduser("~/.sba_chrome_pid")
    if os.path.exists(pid_file):
        import json
        with open(pid_file) as f:
            data = json.load(f)
        try:
            if sys.platform == "win32":
                os.system(f"taskkill /F /PID {data['pid']} 2>nul")
            else:
                os.kill(data["pid"], signal.SIGTERM)
            print(f"Chrome (PID: {data['pid']}) stopped")
        except Exception as e:
            print(f"Error stopping Chrome: {e}")
        os.remove(pid_file)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_chrome()
    else:
        if not start_chrome():
            sys.exit(1)
