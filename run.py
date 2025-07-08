# run.py - First AI Utility Launcher v30.0.0
import sys
import subprocess
from pathlib import Path
import shutil
import time
import threading

# --- Configuration ---
VENV_DIR = Path(__file__).parent / "venv"
# Corrected syntax error on the line below
REQUIREMENTS_FILE = Path(__file__).parent / "requirements.txt"
MAIN_APP_SCRIPT = Path(__file__).parent / "kyo_qa_tool_app.py" # This can be renamed later if needed
MIN_PYTHON_VERSION = (3, 9)

# --- ANSI Colors for "Bling" ---
class Colors:
    KYOCERA_RED = '\033[38;2;227;26;47m' # The official Kyocera red
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """Prints the new stylized ASCII art header for the AI Utility."""
    # ASCII art text: F A I T
    art = r"""
.-----------------------------------------------------------------------.
|      ::::::::::             :::          :::::::::::        :::    :::|
|     :+:                  :+: :+:            :+:            :+:    :+: |
|    +:+                 +:+   +:+           +:+            +:+    +:+  |
|   :#::+::#           +#++:++#++:          +#+            +#+    +:+   |
|  +#+                +#+     +#+          +#+            +#+    +#+    |
| #+#                #+#     #+#          #+#            #+#    #+#     |
|###                ###     ###      ###########         ########       |
'-----------------------------------------------------------------------'
"""
    header = f"""
{Colors.KYOCERA_RED}{art}{Colors.ENDC}
============================================================
    {Colors.BOLD}First AI Utility - Self-Contained & Private{Colors.ENDC}
============================================================
"""
    print(header)

def run_command_with_spinner(command, message):
    """Runs a command silently while showing an engaging spinner message."""
    spinner_chars = ['|', '/', '-', '\\']
    process_done = threading.Event()

    def spin():
        i = 0
        while not process_done.is_set():
            sys.stdout.write(f"\r{Colors.YELLOW}{spinner_chars[i % len(spinner_chars)]}{Colors.ENDC} {message}")
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)

    spinner_thread = threading.Thread(target=spin, daemon=True)
    spinner_thread.start()

    try:
        subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process_done.set()
        spinner_thread.join()
        sys.stdout.write(f"\r{Colors.GREEN}✓{Colors.ENDC} {message}... Done.          \n")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        process_done.set()
        spinner_thread.join()
        sys.stdout.write(f"\r{Colors.RED}✗{Colors.ENDC} {message}... Failed.          \n")
        with open("startup_error.log", "a") as f:
            f.write(f"Error running command {' '.join(map(str, command))}: {e}\n")
        return False

def get_venv_python_path():
    """Gets the path to the Python executable in the virtual environment."""
    return VENV_DIR / "Scripts" / "python.exe" if sys.platform == "win32" else VENV_DIR / "bin" / "python"

def setup_environment():
    """Checks Python version, creates venv, and installs dependencies with better feedback."""
    print_header()

    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"{Colors.RED}✗ Error: Python {'.'.join(map(str, MIN_PYTHON_VERSION))}+ is required. You have {sys.version}{Colors.ENDC}")
        return False

    venv_python = get_venv_python_path()
    if not (VENV_DIR.exists() and venv_python.exists()):
        print(f"{Colors.YELLOW}[INFO] First-time setup detected. This may take several minutes...{Colors.ENDC}")
        if VENV_DIR.exists():
            print("   - Removing incomplete environment...")
            shutil.rmtree(VENV_DIR)
        
        if not run_command_with_spinner([sys.executable, "-m", "venv", str(VENV_DIR)], "Building local environment"):
            return False
        
        print(f"{Colors.YELLOW}[INFO] Installing dependencies and crawlers...{Colors.ENDC}")
        if not run_command_with_spinner([str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], "Calibrating dependencies"):
            return False
    else:
        print(f"{Colors.GREEN}✓ Existing environment detected. Verifying integrity...{Colors.ENDC}")
        time.sleep(1)
    
    print(f"{Colors.GREEN}✓ Environment is ready.{Colors.ENDC}")
    return True

def launch_application():
    """Launches the main GUI application and waits for it to close."""
    print(f"\n{Colors.GREEN}--- Launching Application ---{Colors.ENDC}")
    print("[INFO] The tool is starting. You can minimize this console window.")
    
    venv_python = get_venv_python_path()
    try:
        subprocess.run([str(venv_python), str(MAIN_APP_SCRIPT)], check=True)
        print(f"\n{Colors.GREEN}--- Application Closed Gracefully ---{Colors.ENDC}")
    except subprocess.CalledProcessError:
        print(f"\n{Colors.RED}--- APPLICATION CRASHED ---{Colors.ENDC}")
        print(f"{Colors.YELLOW}The application closed unexpectedly. Check for error messages or logs.{Colors.ENDC}")
    except FileNotFoundError:
        print(f"\n{Colors.RED}--- LAUNCH FAILED ---{Colors.ENDC}")
        print(f"{Colors.YELLOW}Could not find the application script: {MAIN_APP_SCRIPT}{Colors.ENDC}")

if __name__ == "__main__":
    if setup_environment():
        launch_application()
    
    print("\nPress Enter to exit the launcher.")
    input()
