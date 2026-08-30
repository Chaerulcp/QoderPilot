"""
QoderPilot - QODER DESKTOP AUTOMATION
Native account signup and Qoder Desktop login
Version: 1.0.0
Mendukung: macOS, Windows, Linux
Dengan otomatisasi klik tombol Sign In
Menggunakan Playwright dengan stealth
"""

import asyncio
import json
import re
import time
import random
import os
import secrets
import socket
import subprocess
import sys
import shutil
import platform
import sqlite3
import tempfile
import uuid
from contextlib import closing
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

from qoder_creator.proxy import proxy_error_hint, proxy_url

# ================= ANSI COLORS =================
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    MAGENTA = '\033[95m'

def print_color(text, color=Colors.RESET):
    print(f"{color}{text}{Colors.RESET}")

def banner():
    print(f"""
{Colors.CYAN}Ã¢â€¢â€Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢â€”
Ã¢â€¢â€˜     QoderPilot - DESKTOP AUTOMATION                          Ã¢â€¢â€˜
║     Native account signup + Qoder Desktop login                 ║
Ã¢â€¢â€˜     Version: 1.0.0                                           Ã¢â€¢â€˜
Ã¢â€¢â€˜     Support: macOS | Windows | Linux                        Ã¢â€¢â€˜
Ã¢â€¢â€˜     With Stealth + Playwright                               Ã¢â€¢â€˜
Ã¢â€¢Å¡Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â{Colors.RESET}
""")

# ================= PLATFORM DETECTION =================
SYSTEM = platform.system()
IS_MAC = SYSTEM == "Darwin"
IS_WINDOWS = SYSTEM == "Windows"
IS_LINUX = SYSTEM == "Linux"

# ================= KONFIGURASI PER PLATFORM =================
def get_platform_config(platform_type: str = None):
    """
    Mendapatkan konfigurasi untuk platform tertentu
    """
    if platform_type is None:
        platform_type = SYSTEM
    
    configs = {
        "Darwin": {
            "name": "macOS",
            "app_path": "/Applications/Qoder.app",
            "binary_name": "Electron",
            "data_dir": Path.home() / "Library" / "Application Support" / "Qoder",
            "user_dir": Path.home() / ".qoder",
            "cache_dir": Path.home() / "Library" / "Caches" / "Qoder",
            "preferences": Path.home() / "Library" / "Preferences" / "com.qoder.Qoder.plist",
            "saved_state": Path.home() / "Library" / "Saved Application State" / "com.qoder.Qoder.savedState",
            "launch_cmd": "open",
            "launch_args": ["-a", "/Applications/Qoder.app"]
        },
        "Windows": {
            "name": "Windows",
            "app_path_system": "C:/Program Files/Qoder/Qoder.exe",
            "app_path_user": os.path.expandvars("%LOCALAPPDATA%/Qoder/Qoder.exe"),
            "binary_name": "Qoder.exe",
            "data_dir": Path(os.path.expandvars("%APPDATA%/Qoder")),
            "user_dir": Path.home() / ".qoder",
            "cache_dir": Path(os.path.expandvars("%LOCALAPPDATA%/Qoder/Cache")),
            "preferences": Path(os.path.expandvars("%APPDATA%/Qoder/Preferences")),
            "saved_state": None,
            "launch_cmd": "start",
            "launch_args": ["", ""]
        },
        "Linux": {
            "name": "Linux",
            "app_path": "/usr/bin/qoder",
            "app_path_local": "/usr/local/bin/qoder",
            "binary_name": "qoder",
            "data_dir": Path.home() / ".config" / "Qoder",
            "user_dir": Path.home() / ".qoder",
            "cache_dir": Path.home() / ".cache" / "Qoder",
            "preferences": Path.home() / ".config" / "Qoder" / "preferences",
            "saved_state": None,
            "launch_cmd": "qoder",
            "launch_args": []
        }
    }
    
    return configs.get(platform_type, configs.get("Darwin"))

# ================= FILE PATHS =================
QODER_APP_PATH = None
QODER_DATA_DIR = None
QODER_USER_DIR = None
QODER_CACHE_DIR = None
QODER_PREFERENCES = None
QODER_SAVED_STATE = None
QODER_BINARY = None
LAUNCH_CMD = None
LAUNCH_ARGS = []
PLATFORM_NAME = ""
SELECTED_PLATFORM = SYSTEM

QODER_ACCOUNT_STORAGE_KEYS = (
    "aicoding.auth.loginBroadcast",
    "secret://aicoding.auth.creditUsage",
    "secret://aicoding.auth.userInfo",
    "secret://aicoding.auth.userPlan",
)

def init_platform(platform_type: str):
    """Inisialisasi path berdasarkan platform yang dipilih"""
    global QODER_APP_PATH, QODER_DATA_DIR, QODER_USER_DIR, QODER_BINARY
    global LAUNCH_CMD, LAUNCH_ARGS, PLATFORM_NAME, QODER_CACHE_DIR
    global QODER_PREFERENCES, QODER_SAVED_STATE
    
    config = get_platform_config(platform_type)
    PLATFORM_NAME = config.get("name", "Unknown")
    
    if platform_type == "Darwin":
        QODER_APP_PATH = config.get("app_path")
        QODER_BINARY = Path(QODER_APP_PATH) / "Contents" / "MacOS" / config.get("binary_name")
        QODER_DATA_DIR = config.get("data_dir")
        QODER_USER_DIR = config.get("user_dir")
        QODER_CACHE_DIR = config.get("cache_dir")
        QODER_PREFERENCES = config.get("preferences")
        QODER_SAVED_STATE = config.get("saved_state")
        LAUNCH_CMD = config.get("launch_cmd")
        LAUNCH_ARGS = config.get("launch_args", [])
        
    elif platform_type == "Windows":
        system_path = config.get("app_path_system")
        user_path = config.get("app_path_user")
        
        if os.path.exists(system_path):
            QODER_APP_PATH = system_path
        elif os.path.exists(user_path):
            QODER_APP_PATH = user_path
        else:
            QODER_APP_PATH = None
        
        QODER_BINARY = QODER_APP_PATH if QODER_APP_PATH else None
        QODER_DATA_DIR = config.get("data_dir")
        QODER_USER_DIR = config.get("user_dir")
        QODER_CACHE_DIR = config.get("cache_dir")
        QODER_PREFERENCES = config.get("preferences")
        QODER_SAVED_STATE = config.get("saved_state")
        LAUNCH_CMD = config.get("launch_cmd")
        LAUNCH_ARGS = config.get("launch_args", [])
        
    elif platform_type == "Linux":
        if os.path.exists(config.get("app_path")):
            QODER_APP_PATH = config.get("app_path")
        elif os.path.exists(config.get("app_path_local")):
            QODER_APP_PATH = config.get("app_path_local")
        else:
            QODER_APP_PATH = None
        
        QODER_BINARY = QODER_APP_PATH
        QODER_DATA_DIR = config.get("data_dir")
        QODER_USER_DIR = config.get("user_dir")
        QODER_CACHE_DIR = config.get("cache_dir")
        QODER_PREFERENCES = config.get("preferences")
        QODER_SAVED_STATE = config.get("saved_state")
        LAUNCH_CMD = config.get("launch_cmd")
        LAUNCH_ARGS = config.get("launch_args", [])
    
    print_color(f"  [*] Platform: {PLATFORM_NAME}", Colors.CYAN)
    if QODER_BINARY:
        print_color(f"  [*] Binary path: {QODER_BINARY}", Colors.CYAN)
    else:
        print_color(f"  [!] Qoder binary not found!", Colors.RED)

# ================= FILE PATHS =================
SUCCESS_FILE = "qoder_sukses.txt"
AKUN_FILE = "qoder_akun.txt"
API_KEY_FILE = "qoder_api_keys.txt"
FAILED_FILE = "qoder_failed.txt"
LOG_FILE = "qoder_log.txt"

# ================= UTILITY FUNCTIONS =================

def setup_logging():
    """Setup logging configuration"""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            f.write(f"# QoderPilot Log - {datetime.now(timezone.utc).isoformat()}\n")

def write_log(message: str, level: str = "INFO"):
    """Write log message to file"""
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")

def load_accounts():
    """Load accounts from file"""
    try:
        with open(AKUN_FILE) as f:
            return [{
                "email": l.split("|")[0].strip(),
                "password": l.split("|")[1].strip()
            } for l in f if "|" in l and len(l.split("|")) >= 2]
    except FileNotFoundError:
        write_log(f"File {AKUN_FILE} tidak ditemukan", "ERROR")
        return []

def save_success(email, data):
    """Save successful login"""
    with open(SUCCESS_FILE, "a") as f:
        f.write(f"{email}|{json.dumps(data)}|{datetime.now(timezone.utc).isoformat()}\n")
    credits = data.get("credits")
    credit_status = credits if credits is not None else "not verified"
    write_log(f"Success: {email} - Credits: {credit_status}", "SUCCESS")

def save_failed(email, error_msg):
    """Save failed login attempt"""
    with open(FAILED_FILE, "a") as f:
        f.write(f"{email}|{error_msg}|{datetime.now(timezone.utc).isoformat()}\n")
    write_log(f"Failed: {email} - {error_msg}", "ERROR")

def remove_account(email):
    """Remove account from list after successful processing"""
    accs = load_accounts()
    with open(AKUN_FILE, "w") as f:
        for a in accs:
            if a["email"] != email:
                f.write(f"{a['email']}|{a['password']}\n")

def load_processed_emails():
    """Load emails that have been processed successfully"""
    try:
        with open(SUCCESS_FILE, 'r') as f:
            return [line.split('|')[0] for line in f if '|' in line]
    except FileNotFoundError:
        return []

# ================= PLAYWRIGHT HELPER =================

def ensure_playwright_browsers():
    """Pastikan browser Playwright dan Google Chrome terinstall"""
    try:
        import playwright
        from playwright._impl._api_structures import BrowserType
        
        # Cek apakah Google Chrome terinstall (PRIORITAS)
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            'C:/Program Files/Google/Chrome/Application/chrome.exe',
            'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
        ]
        
        chrome_installed = False
        for cp in chrome_paths:
            if os.path.exists(cp):
                chrome_installed = True
                print_color(f"  Ã¢Å“â€¦ Google Chrome found at: {cp}", Colors.GREEN)
                break
        
        if not chrome_installed:
            print_color("  Ã¢Å¡Â Ã¯Â¸Â Google Chrome TIDAK ditemukan!", Colors.YELLOW)
            print_color("  Ã¢â€žÂ¹Ã¯Â¸Â Google Chrome diperlukan untuk login Google yang aman", Colors.YELLOW)
            print_color("  Ã¢â€žÂ¹Ã¯Â¸Â Download: https://www.google.com/chrome/", Colors.CYAN)
        
        if chrome_installed:
            return True

        # Cek apakah chromium sudah terinstall (sebagai fallback)
        if IS_WINDOWS:
            cache_dir = Path(os.getenv("LOCALAPPDATA", "")) / "ms-playwright"
        elif IS_MAC:
            cache_dir = Path.home() / "Library" / "Caches" / "ms-playwright"
        else:
            cache_dir = Path.home() / ".cache" / "ms-playwright"
        
        chromium_installed = False
        if cache_dir.exists():
            for item in cache_dir.iterdir():
                if "chromium" in str(item).lower() and item.is_dir():
                    chromium_installed = True
                    break
        
        if not chromium_installed:
            print_color("  [*] Playwright Chromium belum terinstall. Menginstall sebagai fallback...", Colors.YELLOW)
            print_color("  [*] Ini mungkin memakan waktu beberapa menit...", Colors.YELLOW)
            
            # Install chromium dengan output
            process = subprocess.Popen(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Tampilkan progress
            for line in process.stdout:
                print(f"    {line.strip()}")
            
            process.wait()
            
            if process.returncode == 0:
                print_color("  Ã¢Å“â€¦ Playwright Chromium berhasil diinstall!", Colors.GREEN)
                write_log("Playwright Chromium installed", "INFO")
            else:
                print_color(f"  Ã¢ÂÅ’ Gagal install Chromium. Silakan install manual:", Colors.RED)
                print_color(f"  {sys.executable} -m playwright install chromium", Colors.YELLOW)
                write_log(f"Failed to install Chromium", "ERROR")
        else:
            print_color("  Ã¢Å“â€¦ Playwright Chromium sudah terinstall (fallback)", Colors.GREEN)
        
        return chrome_installed or chromium_installed
            
    except ImportError:
        print_color("  [!] Playwright tidak terinstall. Menginstall...", Colors.YELLOW)
        
        process = subprocess.Popen(
            [sys.executable, "-m", "pip", "install", "playwright"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(f"    {line.strip()}")
        
        process.wait()
        
        if process.returncode == 0:
            print_color("  Ã¢Å“â€¦ Playwright berhasil diinstall!", Colors.GREEN)
            # Install browser
            print_color("  [*] Menginstall browser Chromium...", Colors.YELLOW)
            process = subprocess.Popen(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                print(f"    {line.strip()}")
            
            process.wait()
            
            if process.returncode == 0:
                print_color("  Ã¢Å“â€¦ Browser berhasil diinstall!", Colors.GREEN)
                return True
            else:
                print_color(f"  Ã¢ÂÅ’ Gagal install browser.", Colors.RED)
                return False
        else:
            print_color(f"  Ã¢ÂÅ’ Gagal install playwright.", Colors.RED)
            return False

# ================= QODER PATCHER =================

class QoderPatcher:
    """Handle Qoder app patching for multiple platforms"""
    
    def __init__(self, platform_type: str = None):
        if platform_type is None:
            platform_type = SYSTEM
        self.platform = platform_type
        self.config = get_platform_config(platform_type)
        self.mac_address = None
        self.machine_id = None
        self.ms_deviceid = None
        self.umid = None
        self.is_patched = False
        
    def generate_fake_mac(self):
        """Generate fake MAC address (for macOS)"""
        mac = ':'.join(['{:02x}'.format(random.randint(0x00, 0xff)) for _ in range(6)])
        self.mac_address = mac
        write_log(f"Generated fake MAC: {mac}", "INFO")
        return mac
    
    def generate_machine_id(self):
        """Generate fake machine ID.

        Qoder expects the machineid file to hold a UUID. The previous
        md5-of-small-int value had weak entropy and the wrong shape, so the
        app regenerated it on launch. A UUID v4 matches the native format and
        is far more likely to be kept as-is.
        """
        machine_id = str(uuid.uuid4())
        self.machine_id = machine_id
        write_log(f"Generated machine ID: {machine_id}", "INFO")
        return machine_id
    
    def generate_ms_deviceid(self):
        """Generate fake Microsoft device ID"""
        import uuid
        device_id = str(uuid.uuid4())
        self.ms_deviceid = device_id
        write_log(f"Generated MS device ID: {device_id}", "INFO")
        return device_id
    
    def generate_umid(self):
        """Generate fake UMID"""
        import uuid
        umid = str(uuid.uuid4())
        self.umid = umid
        write_log(f"Generated UMID: {umid}", "INFO")
        return umid
    
    def generate_pkce(self):
        """Generate PKCE code_verifier and code_challenge (S256) for device auth"""
        import hashlib
        import base64
        
        # Generate code_verifier: 32 random bytes, base64url encoded
        code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('ascii')
        
        # Generate code_challenge: SHA256 of code_verifier, base64url encoded
        digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
        
        self.code_verifier = code_verifier
        self.code_challenge = code_challenge
        
        write_log(f"Generated PKCE challenge (S256)", "INFO")
        return code_verifier, code_challenge
    
    def generate_nonce(self):
        """Generate random nonce for OAuth device auth"""
        import uuid
        nonce = uuid.uuid4().hex
        self.nonce = nonce
        write_log(f"Generated nonce: {nonce[:8]}...", "INFO")
        return nonce
    
    def patch_qoder_data(self):
        """Patch Qoder data directory with fake identifiers"""
        global QODER_DATA_DIR, QODER_USER_DIR
        
        print_color("  [*] Patching Qoder data...", Colors.YELLOW)
        write_log("Starting Qoder data patch", "INFO")
        
        try:
            # Generate fake identifiers
            if self.platform == "Darwin":
                self.generate_fake_mac()
                self.generate_machine_id()
                self.generate_ms_deviceid()
                self.generate_umid()
            else:
                self.generate_machine_id()
                self.generate_ms_deviceid()
            
            # Clear and recreate state files
            if QODER_DATA_DIR and QODER_DATA_DIR.exists():
                # Backup existing data (skip socket files)
                backup_dir = QODER_DATA_DIR.parent / "Qoder_backup"
                if not backup_dir.exists():
                    # Copy only regular files, skip sockets
                    for item in QODER_DATA_DIR.rglob('*'):
                        if item.is_file() and not item.is_socket():
                            try:
                                relative_path = item.relative_to(QODER_DATA_DIR)
                                backup_path = backup_dir / relative_path
                                backup_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(item, backup_path)
                            except Exception as e:
                                write_log(f"Skip backup for {item}: {e}", "WARNING")
                    write_log(f"Backup created at {backup_dir}", "INFO")
                    print(f"  [*] Backup created (skipped socket files)")
                
                # Clear state files
                state_files = [
                    QODER_DATA_DIR / "state.vscdb",
                    QODER_DATA_DIR / "machineid",
                    QODER_DATA_DIR / "ms_deviceid",
                    QODER_DATA_DIR / "serviceMachineId"
                ]
                
                for state_file in state_files:
                    if state_file.exists() and state_file.is_file():
                        state_file.unlink()
                        print(f"  [*] Cleared {state_file.name}")
            
            # Create Qoder data directory if it doesn't exist
            if QODER_DATA_DIR:
                QODER_DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            # Create new state files with fake data
            if QODER_DATA_DIR:
                with open(QODER_DATA_DIR / "machineid", 'w') as f:
                    f.write(self.machine_id)
                
                with open(QODER_DATA_DIR / "ms_deviceid", 'w') as f:
                    f.write(self.ms_deviceid)
                
                with open(QODER_DATA_DIR / "serviceMachineId", 'w') as f:
                    f.write(self.machine_id)
            
            # Create/update user data
            if QODER_USER_DIR:
                QODER_USER_DIR.mkdir(parents=True, exist_ok=True)
            
            # Save patch info
            patch_info = {
                "platform": self.platform,
                "machine_id": self.machine_id,
                "ms_deviceid": self.ms_deviceid,
                "patched_at": datetime.now(timezone.utc).isoformat()
            }
            
            if self.platform == "Darwin":
                patch_info["mac_address"] = self.mac_address
                patch_info["umid"] = self.umid
            
            if QODER_DATA_DIR:
                with open(QODER_DATA_DIR / "patch_info.json", 'w') as f:
                    json.dump(patch_info, f, indent=2)
            
            self.is_patched = True
            write_log("Patch completed successfully", "SUCCESS")
            
            print_color("  Ã¢Å“â€¦ Patch + Reset Complete!", Colors.GREEN)
            print_color(f"  Platform: {self.platform}", Colors.CYAN)
            print_color(f"  machineId: {self.machine_id}", Colors.CYAN)
            print_color(f"  ms_deviceid: {self.ms_deviceid}", Colors.CYAN)
            if self.platform == "Darwin":
                print_color(f"  Fake MAC: {self.mac_address}", Colors.CYAN)
                print_color(f"  UMID: {self.umid}", Colors.CYAN)
            
            return True
            
        except Exception as e:
            write_log(f"Patch failed: {e}", "ERROR")
            print_color(f"  [!] Patch failed: {e}", Colors.RED)
            import traceback
            traceback.print_exc()
            return False

# ================= QODER CLIENT AUTOMATION =================

class QoderClientAutomation:
    """Automate Qoder Client for multiple platforms with UI interaction"""

    DEVICE_REDIRECT_SCHEMES = {"qoder"}
    
    def __init__(
        self,
        headless: bool = False,
        platform_type: str = None,
        timeout: int = 120000,
        proxy: Optional[Dict[str, str]] = None,
    ):
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy
        self.process = None
        self.proxy_bridge_process = None
        self.proxy_bridge_control = None
        self.email = None
        self.password = None
        self.credits = 0
        self.platform = platform_type or SYSTEM
        self.patcher = QoderPatcher(self.platform)
        self.binary_path = self.get_qoder_binary_path()
        write_log(f"Initialized QoderClientAutomation (platform={self.platform}, headless={headless})", "INFO")
    
    def check_qoder_installed(self) -> bool:
        """Check if Qoder Client is installed"""
        global QODER_BINARY, QODER_APP_PATH
        
        if self.platform == "Darwin":
            if os.path.exists(QODER_APP_PATH):
                print_color(f"  Ã¢Å“â€¦ Qoder Client found at {QODER_APP_PATH}", Colors.GREEN)
                write_log(f"Qoder Client found at {QODER_APP_PATH}", "INFO")
                return True
            else:
                print_color(f"  Ã¢ÂÅ’ Qoder Client not found at {QODER_APP_PATH}", Colors.RED)
                print_color("  Please download from https://qoder.com/download", Colors.YELLOW)
                return False
                
        elif self.platform == "Windows":
            if QODER_BINARY and os.path.exists(QODER_BINARY):
                print_color(f"  Ã¢Å“â€¦ Qoder Client found at {QODER_BINARY}", Colors.GREEN)
                write_log(f"Qoder Client found at {QODER_BINARY}", "INFO")
                return True
            else:
                print_color("  Ã¢ÂÅ’ Qoder Client not found", Colors.RED)
                print_color("  Please download from https://qoder.com/download", Colors.YELLOW)
                return False
                
        elif self.platform == "Linux":
            if QODER_BINARY and os.path.exists(QODER_BINARY):
                print_color(f"  Ã¢Å“â€¦ Qoder Client found at {QODER_BINARY}", Colors.GREEN)
                write_log(f"Qoder Client found at {QODER_BINARY}", "INFO")
                return True
            else:
                print_color("  Ã¢ÂÅ’ Qoder Client not found", Colors.RED)
                print_color("  Please download from https://qoder.com/download", Colors.YELLOW)
                return False
        
        return False
    
    def get_qoder_version(self) -> Optional[str]:
        """Read the installed version without starting Qoder Desktop."""
        if self.platform == "Darwin":
            try:
                cmd = ["defaults", "read", f"{QODER_APP_PATH}/Contents/Info.plist", "CFBundleShortVersionString"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print_color(f"  [*] Qoder Version: {version}", Colors.CYAN)
                    write_log(f"Qoder version: {version}", "INFO")
                    return version
            except Exception as e:
                write_log(f"Error checking version: {e}", "WARNING")
        elif self.binary_path:
            binary = Path(self.binary_path)
            manifests = [
                binary.parent / "resources" / "app" / "package.json",
                binary.parent.parent / "resources" / "app" / "package.json",
            ]
            for manifest in manifests:
                try:
                    version = json.loads(manifest.read_text(encoding="utf-8")).get("version")
                except (OSError, ValueError):
                    continue
                if version:
                    print_color(f"  [*] Qoder Version: {version}", Colors.CYAN)
                    write_log(f"Qoder version: {version}", "INFO")
                    return str(version)
        return None
    
    def get_qoder_binary_path(self) -> Optional[str]:
        """Get Qoder binary path"""
        global QODER_BINARY
        return QODER_BINARY

    def _proxy_environment(self, proxy_endpoint: Optional[str] = None) -> Dict[str, str]:
        """Return a process environment that keeps Qoder on the job proxy."""
        environment = os.environ.copy()
        if proxy_endpoint:
            url = proxy_endpoint
        elif self.proxy and self.proxy.get("server"):
            url = proxy_url(self.proxy)
        else:
            return environment

        environment["HTTP_PROXY"] = url
        environment["HTTPS_PROXY"] = url
        environment["ALL_PROXY"] = url
        environment["NO_PROXY"] = "localhost,127.0.0.1,::1"
        return environment

    @staticmethod
    def _available_local_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            return int(listener.getsockname()[1])

    def _stop_proxy_bridge(self) -> None:
        process = getattr(self, "proxy_bridge_process", None)
        if process is not None and process.poll() is None:
            process.terminate()
        control = getattr(self, "proxy_bridge_control", None)
        if control is not None:
            try:
                control.unlink(missing_ok=True)
            except OSError:
                pass
        self.proxy_bridge_process = None
        self.proxy_bridge_control = None

    def _start_authenticated_proxy_bridge(self) -> Optional[str]:
        """Start a local relay that injects proxy credentials for the app.

        Used when the job proxy requires authentication, so the desktop app
        never receives credentials on its command line or in environment
        variables. The relay exits automatically when the app closes.
        """
        if not self.proxy:
            return None
        upstream_url = proxy_url(self.proxy)
        if not upstream_url:
            return None

        port = self._available_local_port()
        token = secrets.token_hex(8)
        control = Path(tempfile.gettempdir()) / (
            f"qoderpilot-proxy-bridge-{os.getpid()}-{token}.pids"
        )
        helper = Path(sys.executable)
        pythonw = helper.with_name("pythonw.exe")
        if pythonw.is_file():
            helper = pythonw

        environment = os.environ.copy()
        environment["QODERPILOT_PROXY_BRIDGE_UPSTREAM"] = upstream_url
        command = [
            str(helper),
            "-m",
            "qoder_client.proxy_bridge",
            "--listen-port",
            str(port),
            "--control-file",
            str(control),
        ]
        creation_flags = (
            getattr(subprocess, "CREATE_NO_WINDOW", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
        popen_kwargs: Dict[str, Any] = dict(
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=environment,
            close_fds=True,
        )
        if creation_flags:
            popen_kwargs["creationflags"] = creation_flags
        try:
            process = subprocess.Popen(command, **popen_kwargs)
        except OSError as exc:
            write_log(f"Could not start authenticated proxy bridge: {exc}", "ERROR")
            return None

        self.proxy_bridge_process = process
        self.proxy_bridge_control = control
        for _ in range(50):
            if process.poll() is not None:
                break
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    write_log(
                        f"Authenticated proxy bridge ready on 127.0.0.1:{port}",
                        "SUCCESS",
                    )
                    print_color(
                        "  [OK] Relay autentikasi proxy aktif.",
                        Colors.GREEN,
                    )
                    return f"http://127.0.0.1:{port}"
            except OSError:
                time.sleep(0.1)

        self._stop_proxy_bridge()
        write_log("Authenticated proxy bridge did not become ready", "ERROR")
        return None

    def _set_proxy_bridge_targets(self, process_ids: List[int]) -> bool:
        control = getattr(self, "proxy_bridge_control", None)
        if control is None:
            return True
        try:
            control.write_text(
                "".join(f"{process_id}\n" for process_id in process_ids),
                encoding="utf-8",
            )
        except OSError as exc:
            write_log(f"Could not attach proxy bridge to app process: {exc}", "ERROR")
            self._stop_proxy_bridge()
            return False
        return True
    
    def get_qoder_pid(self) -> Optional[int]:
        """Get Qoder process ID"""
        try:
            if self.platform == "Darwin":
                result = subprocess.run(["pgrep", "-f", "Qoder"], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    return int(result.stdout.strip().split('\n')[0])
            elif self.platform == "Windows":
                result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Qoder.exe"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "Qoder.exe" in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                return int(parts[1])
            elif self.platform == "Linux":
                result = subprocess.run(["pgrep", "-f", "qoder"], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    return int(result.stdout.strip().split('\n')[0])
        except Exception:
            pass
        return None
    
    def kill_qoder_process(self):
        """Kill Qoder process (and its process tree so spawned helpers die too)"""
        try:
            if self.platform == "Darwin":
                subprocess.run(["pkill", "-f", "Qoder"], capture_output=True)
            elif self.platform == "Windows":
                subprocess.run(["taskkill", "/F", "/T", "/IM", "Qoder.exe"], capture_output=True)
            elif self.platform == "Linux":
                subprocess.run(["pkill", "-f", "qoder"], capture_output=True)
            
            write_log("Killed Qoder process", "INFO")
            print("  [*] Killed existing Qoder process")
            time.sleep(2)
        except Exception as e:
            write_log(f"Error killing Qoder: {e}", "WARNING")

    def clear_qoder_account_session(self) -> bool:
        """Remove only the persisted account session before a new login.

        Device patching alone does not sign out Qoder. Account data lives in
        VS Code global storage and SharedClientCache, so it must be cleared
        while Qoder is stopped. User settings, extensions, projects, and chat
        state are intentionally preserved.
        """
        if not QODER_DATA_DIR:
            write_log("Qoder data directory is unavailable for session cleanup", "ERROR")
            return False

        print("  [*] Clearing previous Qoder account session...")
        data_root = Path(QODER_DATA_DIR).resolve()
        user_root = Path(QODER_USER_DIR).resolve() if QODER_USER_DIR else None
        changed = 0

        databases = (
            data_root / "User" / "globalStorage" / "state.vscdb",
            data_root / "User" / "globalStorage" / "state.vscdb.backup",
        )
        placeholders = ",".join("?" for _ in QODER_ACCOUNT_STORAGE_KEYS)

        try:
            for database in databases:
                database.resolve().relative_to(data_root)
                if not database.is_file():
                    continue
                with closing(sqlite3.connect(str(database), timeout=5)) as connection:
                    with connection:
                        cursor = connection.execute(
                            f"DELETE FROM ItemTable WHERE key IN ({placeholders})",
                            QODER_ACCOUNT_STORAGE_KEYS,
                        )
                        changed += max(cursor.rowcount, 0)

            session_files = [
                data_root / "SharedClientCache" / "cache" / "machine_token.json",
                data_root / "SharedClientCache" / "cache" / "status.json",
            ]
            if user_root:
                session_files.append(user_root / ".qoder-app-status.json")

            for session_file in session_files:
                resolved = session_file.resolve()
                allowed_root = user_root if user_root and session_file.parent == user_root else data_root
                resolved.relative_to(allowed_root)
                if resolved.is_file():
                    resolved.unlink()
                    changed += 1

            write_log(f"Cleared previous Qoder account session ({changed} records/files)", "SUCCESS")
            print("  [OK] Previous Qoder account session cleared.")
            return True
        except (OSError, sqlite3.DatabaseError, ValueError) as exc:
            write_log(f"Could not clear previous Qoder account session: {exc}", "ERROR")
            print_color(f"  [!] Failed to clear previous Qoder session: {exc}", Colors.RED)
            return False
    
    def launch_qoder(self) -> bool:
        """Launch Qoder Client"""
        if not self.check_qoder_installed():
            return False
        
        # Kill existing process
        self.kill_qoder_process()

        # A patched machine ID does not remove the previous account token.
        # Clear only authentication state so this run always starts signed out.
        if not self.clear_qoder_account_session():
            return False
        
        # Apply patch before launch
        self.patcher.patch_qoder_data()

        # Detect actual binary
        binary_path = self.binary_path
        if not binary_path:
            print_color("  Ã¢ÂÅ’ Could not find Qoder binary", Colors.RED)
            write_log("Qoder binary not found", "ERROR")
            return False
        
        if not os.path.exists(binary_path):
            print_color(f"  Ã¢ÂÅ’ Binary not found at: {binary_path}", Colors.RED)
            write_log(f"Binary not found: {binary_path}", "ERROR")
            return False

        # Proxies that require authentication cannot be passed straight to
        # Electron via --proxy-server. Route the app through the local bridge
        # instead so credentials are injected by the relay, not exposed.
        proxy_endpoint = self.proxy.get("server") if self.proxy else None
        uses_authenticated_bridge = bool(
            self.proxy and self.proxy.get("server") and self.proxy.get("username")
        )
        if uses_authenticated_bridge:
            proxy_endpoint = self._start_authenticated_proxy_bridge()
            if not proxy_endpoint:
                print_color(
                    "  [!] Relay autentikasi proxy Qoder gagal dimulai.",
                    Colors.RED,
                )
                write_log("Qoder launch aborted: proxy bridge unavailable", "ERROR")
                return False

        try:
            print_color(f"  [*] Launching Qoder Client from: {binary_path}", Colors.YELLOW)
            write_log(f"Launching Qoder Client: {binary_path}", "INFO")
            
            # Launch Qoder with appropriate command
            if self.platform == "Darwin":
                cmd = [
                    binary_path,
                    "--disable-extensions",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            elif self.platform == "Windows":
                cmd = [binary_path]
            else:  # Linux
                cmd = [
                    binary_path,
                    "--disable-extensions",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]

            if proxy_endpoint:
                cmd.append(f"--proxy-server={proxy_endpoint}")
                cmd.append("--proxy-bypass-list=<-loopback>")
                write_log(f"Qoder proxy: {proxy_endpoint}", "INFO")
            
            environment = self._proxy_environment(
                proxy_endpoint if uses_authenticated_bridge else None
            )
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )
            
            time.sleep(8)  # Wait for app to launch
            
            # Check if process is running
            if self.process.poll() is None:
                if uses_authenticated_bridge and not self._set_proxy_bridge_targets(
                    [self.process.pid]
                ):
                    self._stop_proxy_bridge()
                    print_color(
                        "  [!] Relay proxy tidak dapat dipasang ke proses Qoder.",
                        Colors.RED,
                    )
                    return False
                self._verify_machine_id_persisted()
                print_color("  Ã¢Å“â€¦ Qoder Client launched successfully!", Colors.GREEN)
                write_log("Qoder Client launched", "SUCCESS")
                return True
            else:
                self._stop_proxy_bridge()
                print_color("  Ã¢ÂÅ’ Qoder Client failed to launch", Colors.RED)
                return False
                
        except Exception as e:
            self._stop_proxy_bridge()
            write_log(f"Error launching Qoder: {e}", "ERROR")
            print_color(f"  [!] Error launching Qoder: {e}", Colors.RED)
            import traceback
            traceback.print_exc()
            return False
    
    def _verify_machine_id_persisted(self) -> None:
        """Diagnostic: did Qoder keep the patched machine ID after launch?

        The app may rewrite the machineid file on start. This check only
        reports the outcome so logs show whether the patched identity is
        actually being used.
        """
        if not QODER_DATA_DIR:
            return
        patched = getattr(self.patcher, "machine_id", None)
        if not patched:
            return
        machine_file = Path(QODER_DATA_DIR) / "machineid"
        try:
            current = machine_file.read_text(encoding="utf-8").strip()
        except OSError:
            write_log("Machine ID file not readable after launch", "WARNING")
            return
        if current == patched:
            write_log("Patched machine ID retained by Qoder after launch", "SUCCESS")
        else:
            write_log(
                f"Qoder rewrote machine ID after launch "
                f"(patched={patched}, current={current})",
                "WARNING",
            )
    
    def verify_outbound_ip(self) -> Optional[str]:
        """Best-effort check that outbound traffic leaves through the job proxy.

        Informational only: the observed IP is logged, and a mismatch with the
        proxy host produces a warning (rotating proxies legitimately exit from
        a different address). Set QODERPILOT_SKIP_IP_CHECK=1 to disable.
        """
        if str(os.getenv("QODERPILOT_SKIP_IP_CHECK", "")).strip().lower() in {
            "1", "true", "yes", "on",
        }:
            write_log("Outbound IP check skipped (QODERPILOT_SKIP_IP_CHECK)", "INFO")
            return None
        if not self.proxy or not self.proxy.get("server"):
            return None

        import urllib.request

        endpoint = proxy_url(self.proxy)
        proxy_host = urlsplit(endpoint).hostname or ""
        try:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": endpoint, "https": endpoint})
            )
            with opener.open("https://api.ipify.org", timeout=15) as response:
                observed = response.read(1024).decode("utf-8", "replace").strip()
        except Exception as exc:
            hint = proxy_error_hint(exc)
            suffix = f" ({hint})" if hint else ""
            write_log(
                f"Outbound IP check failed via proxy {proxy_host or endpoint}: {exc}{suffix}",
                "WARNING",
            )
            return None

        if not observed:
            write_log("Outbound IP check returned an empty address", "WARNING")
            return None

        if proxy_host and observed.lower() != proxy_host.lower():
            write_log(
                f"Outbound IP {observed} differs from proxy host {proxy_host} "
                "(may be a rotating exit node)",
                "WARNING",
            )
        else:
            write_log(f"Outbound IP via proxy confirmed: {observed}", "SUCCESS")
        print_color(f"  [INFO] IP keluar via proxy: {observed}", Colors.CYAN)
        return observed
    
    # ================= UI AUTOMATION METHODS =================
    
    async def click_signin_with_accessibility(self) -> bool:
        """Klik Sign In menggunakan macOS Accessibility API"""
        if not IS_MAC:
            print_color("  [!] Accessibility API only available on macOS", Colors.YELLOW)
            return False
        
        applescript = '''
        tell application "System Events"
            tell process "Qoder"
                set frontmost to true
                delay 2
                
                -- Cari tombol Sign In
                set signInButton to null
                set allButtons to every button of window 1
                repeat with btn in allButtons
                    set btnTitle to title of btn
                    if btnTitle contains "Sign" or btnTitle contains "sign" then
                        set signInButton to btn
                        exit repeat
                    end if
                end repeat
                
                if signInButton is not null then
                    click signInButton
                    return "found_by_title"
                end if
                
                -- Fallback: cari berdasarkan deskripsi
                set allUIElements to every UI element of window 1
                repeat with elem in allUIElements
                    set elemDescription to description of elem
                    if elemDescription contains "Sign" or elemDescription contains "sign" then
                        click elem
                        return "found_by_description"
                    end if
                end repeat
                
                -- Fallback: cari berdasarkan posisi (pojok kanan atas)
                tell window 1
                    set windowSize to size
                    set windowWidth to item 1 of windowSize
                    set windowHeight to item 2 of windowSize
                    set signInX to windowWidth - 80
                    set signInY to 25
                    click at {signInX, signInY}
                    return "clicked_at_position"
                end tell
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=15)
            output = result.stdout.strip()
            if "found" in output or "clicked" in output:
                print_color(f"  Ã¢Å“â€¦ Sign In clicked! ({output})", Colors.GREEN)
                write_log(f"Sign In clicked via Accessibility: {output}", "INFO")
                return True
            else:
                print_color(f"  Ã¢Å¡Â Ã¯Â¸Â Sign In not found: {output}", Colors.YELLOW)
                return False
        except subprocess.TimeoutExpired:
            print_color("  Ã¢Å¡Â Ã¯Â¸Â Accessibility timeout", Colors.YELLOW)
            return False
        except Exception as e:
            write_log(f"Accessibility error: {e}", "ERROR")
            print_color(f"  [!] Accessibility error: {e}", Colors.RED)
            return False
    
    async def click_signin_with_coordinates(self) -> bool:
        """Klik Sign In menggunakan koordinat presisi di macOS"""
        if not IS_MAC:
            return False
        
        applescript = '''
        tell application "System Events"
            tell process "Qoder"
                set frontmost to true
                delay 1
                
                tell window 1
                    -- Dapatkan posisi window
                    set windowPosition to position
                    set windowSize to size
                    
                    set windowX to item 1 of windowPosition
                    set windowY to item 2 of windowPosition
                    set windowWidth to item 1 of windowSize
                    set windowHeight to item 2 of windowSize
                    
                    -- Koordinat tombol Sign In (pojok kanan atas)
                    -- Biasanya di sekitar (windowWidth - 80, 25)
                    set signInX to windowX + windowWidth - 80
                    set signInY to windowY + 25
                    
                    click at {signInX, signInY}
                    return "clicked_at_position"
                end tell
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=10)
            if "clicked" in result.stdout:
                print_color("  Ã¢Å“â€¦ Sign In clicked using coordinates!", Colors.GREEN)
                return True
            else:
                print_color("  Ã¢Å¡Â Ã¯Â¸Â Could not click using coordinates", Colors.YELLOW)
                return False
        except Exception as e:
            write_log(f"Coordinate click error: {e}", "ERROR")
            return False
    
    async def click_signin_pyautogui(self) -> bool:
        """Klik Sign In menggunakan pyautogui dengan image recognition"""
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            
            # Cari Qoder window
            try:
                qoder_windows = pyautogui.getWindowsWithTitle("Qoder")
                if qoder_windows:
                    window = qoder_windows[0]
                    window.activate()
                    time.sleep(1)
                    
                    # Cari tombol Sign In dengan image recognition
                    try:
                        sign_in_location = pyautogui.locateOnScreen('sign_in_button.png', confidence=0.7)
                        if sign_in_location:
                            center_x = sign_in_location.left + sign_in_location.width // 2
                            center_y = sign_in_location.top + sign_in_location.height // 2
                            pyautogui.click(center_x, center_y)
                            print_color("  Ã¢Å“â€¦ Sign In clicked using image recognition!", Colors.GREEN)
                            return True
                    except:
                        pass
                    
                    # Fallback: klik berdasarkan posisi relatif window
                    window_x, window_y = window.topleft
                    window_width, window_height = window.size
                    click_x = window_x + window_width - 80
                    click_y = window_y + 25
                    pyautogui.click(click_x, click_y)
                    print_color("  Ã¢Å“â€¦ Sign In clicked using relative position!", Colors.GREEN)
                    return True
                else:
                    print_color("  Ã¢Å¡Â Ã¯Â¸Â Qoder window not found", Colors.YELLOW)
                    return False
            except:
                # Jika getWindowsWithTitle tidak tersedia
                pyautogui.click(1500, 30)  # Default position untuk Mac
                print_color("  Ã¢Å“â€¦ Sign In clicked using default position!", Colors.GREEN)
                return True
                
        except ImportError:
            print_color("  Ã¢Å¡Â Ã¯Â¸Â pyautogui not installed. Install with: pip install pyautogui pillow", Colors.YELLOW)
            return False
        except Exception as e:
            write_log(f"pyautogui error: {e}", "ERROR")
            return False
    
    async def click_signin_button(self) -> bool:
        """Klik Sign In button dengan multiple methods"""
        print_color("  [*] Clicking Sign In button...", Colors.CYAN)
        
        # Try methods in order of reliability
        methods = [
            ("Accessibility API", self.click_signin_with_accessibility),
            ("Coordinates", self.click_signin_with_coordinates),
        ]
        
        # Add pyautogui if installed
        try:
            import pyautogui
            methods.append(("PyAutoGUI", self.click_signin_pyautogui))
        except ImportError:
            pass
        
        for method_name, method in methods:
            print(f"  [*] Trying: {method_name}...")
            success = await method()
            if success:
                write_log(f"Sign In clicked using {method_name}", "INFO")
                await asyncio.sleep(2)
                return True
        
        print_color("  Ã¢Å¡Â Ã¯Â¸Â All automation methods failed", Colors.YELLOW)
        print_color("  Ã¢â€žÂ¹Ã¯Â¸Â Please click 'Sign In' manually in Qoder Desktop", Colors.CYAN)
        return False
    
    def _scan_macos_browser_url(self) -> Optional[str]:
        """
        Scan ALL Chrome tabs (not just the active one) for the Qoder device auth URL.
        This is more reliable than checking only the active tab of the front window,
        since Qoder Desktop opens the URL in a new tab that may not be focused.
        """
        if self.platform != "Darwin":
            return None
        
        applescript = '''
        tell application "Google Chrome"
            if it is running then
                set qoderURL to ""
                repeat with w in windows
                    repeat with t in tabs of w
                        try
                            set tabURL to URL of t
                            if tabURL contains "qoder.com/device/selectAccounts" or tabURL contains "qoder.com/users/sign-in" then
                                set qoderURL to tabURL
                                exit repeat
                            end if
                        end try
                    end repeat
                    if qoderURL is not "" then exit repeat
                end repeat
                return qoderURL
            end if
        end tell
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                url = result.stdout.strip()
                device_url = self._extract_device_auth_url(url)
                if device_url:
                    write_log("Captured valid Qoder PKCE URL from Chrome", "INFO")
                    return device_url
        except Exception as e:
            write_log(f"Error scanning Chrome tabs: {e}", "WARNING")
        
        return None

    @classmethod
    def _is_valid_device_auth_url(cls, url: str) -> bool:
        """Validate that a URL contains the PKCE session owned by Qoder Desktop."""
        try:
            parsed = urlsplit(url)
            params = parse_qs(parsed.query)
        except ValueError:
            return False
        host = (parsed.hostname or "").lower()
        valid_host = host == "qoder.com" or host.endswith(".qoder.com")
        required = {"nonce", "challenge", "challenge_method", "redirect_uri"}
        return (
            parsed.scheme == "https"
            and valid_host
            and parsed.path.rstrip("/").endswith("/device/selectAccounts")
            and required.issubset(params)
            and params["challenge_method"] == ["S256"]
            and urlsplit(params["redirect_uri"][0]).scheme in cls.DEVICE_REDIRECT_SCHEMES
        )

    @classmethod
    def _extract_device_auth_url(cls, browser_url: str) -> Optional[str]:
        """Extract the original device URL from Qoder's sign-in redirect."""
        if cls._is_valid_device_auth_url(browser_url):
            return browser_url
        try:
            parsed = urlsplit(browser_url)
            query = parse_qs(parsed.query)
            callback = (query.get("oauth_callback") or [""])[0]
            origin = f"{parsed.scheme}://{parsed.netloc}"
            candidate = urljoin(origin, callback)
        except (IndexError, ValueError):
            return None
        return candidate if cls._is_valid_device_auth_url(candidate) else None

    def _scan_windows_browser_url(self) -> Optional[str]:
        """Copy the active Qoder URL from a Windows browser address bar."""
        try:
            import pyautogui
            import pyperclip
        except ImportError:
            return None

        previous_clipboard = pyperclip.paste()
        browser_names = ("Google Chrome", "Microsoft Edge", "Brave", "Firefox")
        try:
            windows = [
                window for window in pyautogui.getAllWindows()
                if any(name in window.title for name in browser_names)
            ]
            for window in reversed(windows):
                seen_urls: set[str] = set()
                for _ in range(5):
                    url = self._copy_active_browser_url(window, pyautogui, pyperclip)
                    if url in seen_urls:
                        break
                    seen_urls.add(url)
                    device_url = self._extract_device_auth_url(url)
                    if device_url:
                        pyautogui.hotkey("ctrl", "w")
                        write_log("Captured valid Qoder PKCE URL from browser", "INFO")
                        return device_url
                    pyautogui.hotkey("ctrl", "tab")
                    time.sleep(0.1)
        except Exception as exc:
            write_log(f"Windows browser URL capture failed: {exc}", "WARNING")
        finally:
            pyperclip.copy(previous_clipboard)
        return None

    @staticmethod
    def _copy_active_browser_url(window, pyautogui, pyperclip) -> str:
        try:
            if getattr(window, "isMinimized", False):
                window.restore()
            try:
                window.activate()
            except Exception:
                pass
            pyautogui.click(window.left + (window.width // 2), window.top + 50)
            time.sleep(0.3)
            pyperclip.copy("")
            pyautogui.hotkey("ctrl", "l")
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.2)
            return pyperclip.paste().strip()
        except Exception:
            return ""

    def scan_chrome_for_qoder_url(self) -> Optional[str]:
        """Capture and validate the device URL created by Qoder Desktop."""
        if self.platform == "Darwin":
            return self._scan_macos_browser_url()
        if self.platform == "Windows":
            return self._scan_windows_browser_url()
        return None
    
    def check_qoder_logged_in(self) -> bool:
        """Cek apakah Qoder Desktop sudah login"""
        # Cek dari state files
        if QODER_DATA_DIR:
            try:
                state_file = QODER_DATA_DIR / "state.vscdb"
                if state_file.exists():
                    if state_file.stat().st_size > 10000:
                        return True
            except:
                pass
            
            session_file = QODER_DATA_DIR / "session.json"
            if session_file.exists():
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                        if data.get('token') or data.get('session'):
                            return True
                except:
                    pass
            
            login_file = QODER_DATA_DIR / "login-state.json"
            if login_file.exists():
                try:
                    with open(login_file, 'r') as f:
                        data = json.load(f)
                        if data.get('isLoggedIn') or data.get('logged_in'):
                            return True
                except:
                    pass
        
        # Cek dari process
        pid = self.get_qoder_pid()
        if pid:
            try:
                if self.platform == "Darwin":
                    result = subprocess.run(["lsof", "-p", str(pid), "-i"], capture_output=True, text=True, timeout=5)
                    if "qoder" in result.stdout.lower() and ("https" in result.stdout.lower() or "443" in result.stdout.lower()):
                        return True
            except:
                pass
        
        # Cek via AppleScript: jika window Qoder tidak memiliki tombol "Sign In",
        # kemungkinan sudah login
        if self.platform == "Darwin":
            try:
                applescript = '''
                tell application "System Events"
                    if (exists process "Qoder") then
                        tell process "Qoder"
                            set signInExists to false
                            try
                                set allButtons to every button of window 1
                                repeat with btn in allButtons
                                    if title of btn contains "Sign" then
                                        set signInExists to true
                                        exit repeat
                                    end if
                                end repeat
                            end try
                            return signInExists
                        end tell
                    end if
                end tell
                '''
                result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=5)
                output = result.stdout.strip().lower()
                # If "Sign In" button is NOT found (false), user might be logged in
                if output == "false" and self.get_qoder_pid():
                    return True
            except:
                pass
        
        return False
    
    # ================= LOGIN METHODS =================
    
    def _client_browser_options(self) -> Dict[str, Any]:
        """Build browser options for native Qoder authentication."""
        from qoder_creator.stealth import CHROMIUM_ARGS

        options: Dict[str, Any] = {
            "headless": self.headless,
            "args": CHROMIUM_ARGS.copy(),
        }
        chrome_paths = [
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
        chrome = next((path for path in chrome_paths if os.path.exists(path)), None)
        if chrome:
            options["executable_path"] = chrome
        if self.proxy and self.proxy.get("server"):
            options["proxy"] = self.proxy
        return options

    @staticmethod
    async def _first_visible(page, selectors: List[str], timeout: int = 15000):
        """Return the first visible locator from a bounded selector list."""
        deadline = asyncio.get_running_loop().time() + (timeout / 1000)
        while asyncio.get_running_loop().time() < deadline:
            for selector in selectors:
                locator = page.locator(selector).first
                try:
                    if await locator.is_visible():
                        return locator
                except Exception:
                    continue
            await page.wait_for_timeout(250)
        return None

    @staticmethod
    async def _native_error_text(page) -> str:
        selectors = [
            ".ant-form-item-explain-error:visible",
            "[role='alert']:visible",
            ".ant-message-error:visible",
        ]
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if await locator.is_visible():
                    return " ".join((await locator.inner_text()).split())
            except Exception:
                continue
        return ""

    async def _open_native_login_page(self, page, login_url: str) -> bool:
        """Open Qoder's device URL without leaving the Qoder domain."""
        for strategy in ("domcontentloaded", "load"):
            try:
                await page.goto(login_url, wait_until=strategy, timeout=60000)
                await page.wait_for_timeout(1500)
                if "accounts.google.com" in page.url:
                    write_log("Native auth unexpectedly redirected to Google", "ERROR")
                    return False
                return True
            except Exception as exc:
                write_log(f"Native auth navigation ({strategy}) failed: {exc}", "WARNING")
        return False

    async def _submit_native_credentials(self, page, email: str, password: str) -> bool:
        """Complete Qoder's email step followed by its password step."""
        email_input = await self._first_visible(
            page,
            ["#basic_email:visible", "input[placeholder='Enter your email address']:visible"],
        )
        if email_input is None:
            write_log(f"Native email field not found at {page.url}", "ERROR")
            return False

        print("  [*] Mengisi email akun Qoder...")
        await email_input.fill(email)
        continue_button = await self._first_visible(
            page,
            ["button:has-text('Continue'):visible", "button[type='submit']:visible"],
        )
        if continue_button is None:
            write_log("Native Continue button not found", "ERROR")
            return False
        await continue_button.click()

        password_input = await self._first_visible(
            page,
            [
                "#password_password:visible",
                "input[placeholder='Enter your password']:visible",
                "input[type='password']:visible",
            ],
            timeout=20000,
        )
        if password_input is None:
            error = await self._native_error_text(page)
            write_log(f"Native password step unavailable: {error or page.url}", "ERROR")
            return False

        print("  [*] Mengisi password akun Qoder...")
        await password_input.fill(password)
        sign_in_button = await self._first_visible(
            page,
            ["button:has-text('Sign in'):visible", "button[type='submit']:visible"],
        )
        if sign_in_button is None:
            write_log("Native Sign in button not found", "ERROR")
            return False
        await sign_in_button.click()
        await page.wait_for_timeout(1500)
        return await self._solve_native_login_captcha(page)

    async def _solve_native_login_captcha(self, page) -> bool:
        """Solve the slider only when Qoder presents one during sign-in."""
        trigger = await self._first_visible(
            page,
            ["#aliyunCaptcha-captcha-body:visible", "button:has-text('Click to verify'):visible"],
            timeout=2500,
        )
        if trigger is None:
            return True

        print("  [*] Menyelesaikan captcha login Qoder...")
        try:
            await trigger.click()
        except Exception:
            pass
        await page.wait_for_timeout(1000)
        from qoder_creator.captcha import solve_slider_local

        solved = await solve_slider_local(page, max_attempts=5)
        if not solved:
            write_log("Native Qoder login captcha failed", "ERROR")
            return False
        submit = await self._first_visible(
            page,
            ["button:has-text('Sign in'):visible", "button[type='submit']:visible"],
            timeout=2500,
        )
        if submit is not None:
            await submit.click()
        return True

    @staticmethod
    def _register_redirect_capture(page, state: Dict[str, Optional[str]]) -> None:
        def capture_url(url: str) -> None:
            if url.startswith("qoder://"):
                state["url"] = url

        page.on("request", lambda request: capture_url(request.url))
        page.on("framenavigated", lambda frame: capture_url(frame.url))

    async def _captured_js_redirect(self, page) -> Optional[str]:
        try:
            value = await page.evaluate("window.__qoder_redirect_url || null")
        except Exception:
            return None
        return value if isinstance(value, str) and value.startswith("qoder://") else None

    async def _click_device_confirmation(self, page) -> bool:
        selectors = [
            "button:has-text('Open Qoder'):visible",
            "button:has-text('Continue'):visible",
            "button:has-text('Confirm'):visible",
            "button:has-text('Select'):visible",
        ]
        button = await self._first_visible(page, selectors, timeout=1000)
        if button is None:
            return False
        await button.click()
        return True

    async def _wait_for_qoder_redirect(
        self,
        page,
        state: Dict[str, Optional[str]],
        timeout: int = 90000,
    ) -> Optional[str]:
        deadline = asyncio.get_running_loop().time() + (timeout / 1000)
        confirmation_clicked = False
        while asyncio.get_running_loop().time() < deadline:
            if state.get("url"):
                return state["url"]
            captured = await self._captured_js_redirect(page)
            if captured:
                return captured

            current_url = page.url
            if current_url.startswith("qoder://"):
                return current_url
            if "accounts.google.com" in current_url:
                write_log("Email auth left Qoder and reached Google; refusing credentials", "ERROR")
                return None
            if "signin/rejected" in current_url:
                write_log("Native Qoder sign-in was rejected", "ERROR")
                return None
            if "/device/selectAccounts" in current_url and not confirmation_clicked:
                confirmation_clicked = await self._click_device_confirmation(page)
            error = await self._native_error_text(page)
            if error and "password" in error.lower():
                write_log(f"Native Qoder sign-in error: {error}", "ERROR")
                return None
            await page.wait_for_timeout(500)
        write_log("Timed out waiting for qoder:// redirect", "ERROR")
        return None

    def _open_qoder_protocol(self, url: str) -> bool:
        """Open the authenticated qoder:// callback with the OS protocol handler."""
        if not url.startswith("qoder://"):
            return False
        try:
            if self.platform == "Windows":
                os.startfile(url)  # type: ignore[attr-defined]
            elif self.platform == "Darwin":
                subprocess.run(["open", url], check=True, capture_output=True)
            else:
                subprocess.run(["xdg-open", url], check=True, capture_output=True)
        except (OSError, subprocess.SubprocessError) as exc:
            write_log(f"Failed to open qoder:// callback: {exc}", "ERROR")
            return False
        write_log("Opened authenticated qoder:// callback", "SUCCESS")
        return True

    async def _save_native_login_diagnostic(self, page) -> None:
        try:
            output = Path(LOG_FILE).parent / "native_login_failed.png"
            await page.screenshot(path=str(output), full_page=True)
            write_log(f"Native login diagnostic saved to {output}", "INFO")
        except Exception as exc:
            write_log(f"Could not save native login diagnostic: {exc}", "WARNING")

    async def login_via_browser(
        self,
        email: str,
        password: str,
        device_auth_url: Optional[str] = None,
    ) -> bool:
        """Authenticate a native Qoder account and hand it back to Qoder Desktop."""
        print_color("  [*] Login native Qoder dengan email/password...", Colors.CYAN)
        write_log(f"Starting native Qoder browser login for {email}", "INFO")
        if not ensure_playwright_browsers():
            write_log("Playwright browser is unavailable", "ERROR")
            return False

        try:
            from playwright.async_api import async_playwright
            from qoder_creator.stealth import create_stealth_context

            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(**self._client_browser_options())
                try:
                    context = await create_stealth_context(browser, self.proxy)
                    page = await context.new_page()
                    state: Dict[str, Optional[str]] = {"url": None}
                    self._register_redirect_capture(page, state)
                    login_url = device_auth_url or "https://qoder.com/device/selectAccounts"
                    if not await self._open_native_login_page(page, login_url):
                        await self._save_native_login_diagnostic(page)
                        return False
                    if not await self._submit_native_credentials(page, email, password):
                        await self._save_native_login_diagnostic(page)
                        return False

                    print("  [*] Menunggu callback autentikasi Qoder Desktop...")
                    callback = await self._wait_for_qoder_redirect(page, state)
                    if callback is None:
                        await self._save_native_login_diagnostic(page)
                        return False
                    return self._open_qoder_protocol(callback)
                finally:
                    try:
                        await browser.close()
                    except Exception as exc:
                        write_log(f"Browser cleanup warning: {exc}", "WARNING")
        except Exception as exc:
            write_log(f"Native Qoder browser login failed: {exc}", "ERROR")
            print_color(f"  [!] Login native Qoder gagal: {exc}", Colors.RED)
            return False

    def _close_stale_auth_tabs(self) -> int:
        """Close old Qoder auth tabs before creating a new desktop session."""
        if self.platform != "Windows":
            return 0
        closed = 0
        for _ in range(5):
            if not self._scan_windows_browser_url():
                break
            closed += 1
        if closed:
            write_log(f"Closed {closed} stale Qoder auth tab(s)", "INFO")
        return closed

    async def _capture_device_auth_url(self, attempts: int = 6) -> Optional[str]:
        for _ in range(attempts):
            await asyncio.sleep(1)
            device_url = self.scan_chrome_for_qoder_url()
            if device_url:
                write_log("Captured current Qoder Desktop PKCE session", "SUCCESS")
                return device_url
        return None

    async def _obtain_device_auth_url(self) -> Optional[str]:
        """Trigger one login session and capture only its newly opened URL."""
        # Windows always uses an explicit manual gate. Do not inspect browser
        # tabs or guess a click coordinate before the user confirms that the
        # newly-created Qoder login tab is open. Some terminals incorrectly
        # report isatty() as False, so this branch must not depend on it.
        if self.platform == "Windows":
            print_color("  [ACTION] Klik 'Sign In' pada Qoder Desktop.", Colors.CYAN)
            print("  [*] Tunggu sampai tab login Qoder terbuka di browser.")
            try:
                input(f"{Colors.YELLOW}Tekan Enter setelah tab login sudah terbuka...{Colors.RESET}")
            except EOFError:
                write_log("Windows manual login requires an interactive Enter confirmation", "ERROR")
                print_color("  [!] Terminal tidak dapat menerima tombol Enter.", Colors.RED)
                return None
            print("  [*] Mencari URL PKCE dari tab login yang baru...")
            return await self._capture_device_auth_url(attempts=10)

        self._close_stale_auth_tabs()
        clicked = await self.click_signin_button()
        if clicked:
            device_url = await self._capture_device_auth_url()
            if device_url:
                return device_url
        if not sys.stdin.isatty():
            return None

        print_color("  [!] Tombol Sign In belum berhasil dibuka otomatis.", Colors.YELLOW)
        print("  [*] Klik Sign In pada Qoder yang sedang terbuka.")
        print("  [*] Tunggu sampai tab login terbuka; jangan tutup atau membuka ulang Qoder.")
        input(f"{Colors.YELLOW}Tekan Enter setelah tab login sudah terbuka...{Colors.RESET}")
        print("  [*] Mencari URL PKCE dari tab login yang baru...")
        return await self._capture_device_auth_url(attempts=10)

    @staticmethod
    def _auth_log_checkpoint() -> tuple[Optional[Path], int]:
        if not QODER_DATA_DIR:
            return None, 0
        try:
            logs = list((Path(QODER_DATA_DIR) / "logs").rglob("renderer.log"))
            latest = max(logs, key=lambda path: path.stat().st_mtime)
            return latest, latest.stat().st_size
        except (OSError, ValueError):
            return None, 0

    @staticmethod
    def _auth_log_status(checkpoint: tuple[Optional[Path], int]) -> Optional[bool]:
        path, offset = checkpoint
        if path is None:
            return None
        try:
            with path.open("rb") as stream:
                stream.seek(offset)
                content = stream.read().decode("utf-8", errors="replace")
        except OSError:
            return None
        success = content.rfind("[QoderPkceLoginService] Login completed for user:")
        failure = max(content.rfind("Login failed ["), content.rfind("Login cancelled"))
        if success < 0 and failure < 0:
            return None
        return success > failure

    async def _wait_for_desktop_auth(
        self,
        checkpoint: tuple[Optional[Path], int],
        timeout: int = 90,
    ) -> bool:
        for elapsed in range(timeout):
            status = self._auth_log_status(checkpoint)
            if status is not None:
                return status
            if elapsed and elapsed % 15 == 0:
                print(f"  [*] Menunggu konfirmasi Qoder Desktop... ({elapsed}/{timeout})")
            await asyncio.sleep(1)
        write_log("Timed out waiting for Qoder Desktop PKCE completion", "ERROR")
        return False

    async def login_to_qoder_client(self, email: str, password: str) -> bool:
        """Keep one Qoder process alive for the complete PKCE login session."""
        self.email = email
        self.password = password
        print_color(f"\n[LOGIN] Qoder Desktop: {email}", Colors.YELLOW)
        write_log(f"Attempting login to Qoder Client: {email}", "INFO")

        if not self.launch_qoder():
            return False
        print("  [*] Menunggu Qoder Desktop siap...")
        await asyncio.sleep(5)

        checkpoint = self._auth_log_checkpoint()
        device_auth_url = await self._obtain_device_auth_url()
        if not device_auth_url:
            write_log("Could not capture a new Qoder Desktop PKCE URL", "ERROR")
            print_color("  [!] URL PKCE sesi Qoder yang aktif tidak ditemukan.", Colors.RED)
            return False

        print_color("  [OK] URL PKCE sesi Qoder aktif berhasil ditangkap.", Colors.GREEN)
        if not await self.login_via_browser(email, password, device_auth_url):
            return False

        print("  [*] Menunggu Qoder Desktop menerima token...")
        if await self._wait_for_desktop_auth(checkpoint):
            print_color("  [OK] Qoder Desktop berhasil login.", Colors.GREEN)
            write_log(f"Qoder Desktop PKCE login completed for {email}", "SUCCESS")
            return True

        print_color("  [!] Qoder Desktop tidak mengonfirmasi login.", Colors.RED)
        write_log(f"Qoder Desktop did not confirm login for {email}", "ERROR")
        return False

    async def check_credits_after_login(self) -> Optional[int]:
        """Read a local credit snapshot when Qoder has written one."""
        if QODER_USER_DIR:
            try:
                settings_file = QODER_USER_DIR / "settings.json"
                if settings_file.exists():
                    with open(settings_file, 'r') as f:
                        data = json.load(f)
                        credits = data.get("credits")
                        if isinstance(credits, int) and not isinstance(credits, bool):
                            return credits
            except Exception:
                pass
        
        if QODER_DATA_DIR:
            credits_file = QODER_DATA_DIR / "credits.json"
            if credits_file.exists():
                try:
                    with open(credits_file, 'r') as f:
                        data = json.load(f)
                        credits = data.get("credits")
                        if isinstance(credits, int) and not isinstance(credits, bool):
                            return credits
                except Exception:
                    pass
        
        return None
    
    async def run_client_login(
        self,
        email: str,
        password: str,
    ) -> Optional[Dict[str, Any]]:
        """Log in to Qoder Desktop and report only locally verified credit data."""
        print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
        print(f"{Colors.CYAN}QODER DESKTOP LOGIN: {email}{Colors.RESET}")
        print(f"{Colors.CYAN}Platform: {PLATFORM_NAME}{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
        write_log(f"Starting Qoder Client login for {email}", "INFO")
        if self.proxy and self.proxy.get("server"):
            print_color(f"Proxy: {self.proxy['server']}", Colors.CYAN)
            await asyncio.to_thread(self.verify_outbound_ip)

        if not self.check_qoder_installed():
            return None
        self.get_qoder_version()
        if self.binary_path:
            print_color(f"  [*] Binary path: {self.binary_path}", Colors.CYAN)
        if not await self.login_to_qoder_client(email, password):
            save_failed(email, "Login failed")
            return None

        credits = await self.check_credits_after_login()
        if credits is None:
            print_color("  [INFO] Credits tidak dapat diverifikasi dari data lokal.", Colors.YELLOW)
            print("  [*] Periksa Qoder: Settings > Usage.")
        else:
            print_color(f"  [INFO] Snapshot credits lokal: {credits}", Colors.CYAN)
            print("  [*] Konfirmasi nilai aktual di Qoder: Settings > Usage.")

        data = {
            "credits": credits,
            "email": email,
            "client_login": True,
            "platform": PLATFORM_NAME,
        }
        save_success(email, data)
        remove_account(email)
        return {"success": True, "credits": credits}
# ================= RESET FUNCTIONS =================

def reset_qoder_deep():
    """Deep reset - menghapus semua data Qoder termasuk cache dan preferences"""
    print_color("\n[*] Deep resetting Qoder...", Colors.YELLOW)
    write_log("Starting deep reset", "INFO")
    
    # Kill Qoder process first
    try:
        if IS_MAC:
            subprocess.run(["pkill", "-f", "Qoder"], capture_output=True)
        elif IS_WINDOWS:
            subprocess.run(["taskkill", "/F", "/IM", "Qoder.exe"], capture_output=True)
        elif IS_LINUX:
            subprocess.run(["pkill", "-f", "qoder"], capture_output=True)
        print("  [*] Killed Qoder processes")
        time.sleep(2)
    except Exception as e:
        write_log(f"Error killing Qoder: {e}", "WARNING")
    
    # Data directories to clean
    data_dirs = [
        QODER_DATA_DIR,
        QODER_USER_DIR,
        QODER_CACHE_DIR,
    ]
    
    for dir_path in data_dirs:
        if dir_path and dir_path.exists():
            try:
                shutil.rmtree(dir_path, ignore_errors=True)
                print(f"  Ã¢Å“â€¦ Removed: {dir_path}")
                write_log(f"Removed {dir_path}", "INFO")
            except Exception as e:
                print(f"  [!] Could not remove {dir_path}: {e}")
                write_log(f"Could not remove {dir_path}: {e}", "WARNING")
    
    # Remove preferences files
    if QODER_PREFERENCES and QODER_PREFERENCES.exists():
        try:
            if QODER_PREFERENCES.is_file():
                QODER_PREFERENCES.unlink()
            else:
                shutil.rmtree(QODER_PREFERENCES, ignore_errors=True)
            print(f"  Ã¢Å“â€¦ Removed preferences: {QODER_PREFERENCES}")
        except Exception as e:
            print(f"  [!] Could not remove preferences: {e}")
    
    # Remove saved state (macOS)
    if QODER_SAVED_STATE and QODER_SAVED_STATE.exists():
        try:
            shutil.rmtree(QODER_SAVED_STATE, ignore_errors=True)
            print(f"  Ã¢Å“â€¦ Removed saved state: {QODER_SAVED_STATE}")
        except Exception as e:
            print(f"  [!] Could not remove saved state: {e}")
    
    # Recreate directories
    if QODER_DATA_DIR:
        QODER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"  Ã¢Å“â€¦ Recreated: {QODER_DATA_DIR}")
    
    if QODER_USER_DIR:
        QODER_USER_DIR.mkdir(parents=True, exist_ok=True)
        print(f"  Ã¢Å“â€¦ Recreated: {QODER_USER_DIR}")
    
    print_color("  Ã¢Å“â€¦ Deep reset complete!", Colors.GREEN)
    write_log("Deep reset completed", "SUCCESS")
    return True

def force_remove_tree(path) -> bool:
    """Remove a directory tree, surviving read-only files and brief locks.

    The fallback walk is bottom-up: children must be removed before their
    parents, otherwise Windows raises WinError 145 ("The directory is not
    empty") when rmdir reaches a directory whose children were skipped.
    """
    path = Path(path)
    if not path.exists():
        return True

    def _clear_readonly(func, target, exc_info):
        try:
            os.chmod(target, 0o777)
            func(target)
        except OSError:
            pass

    try:
        shutil.rmtree(path, onerror=_clear_readonly)
    except OSError as exc:
        write_log(f"Removal retry needed for {path}: {exc}", "WARNING")

    if not path.exists():
        print(f"  [OK] Removed: {path}")
        return True

    # Give Windows a moment to release handles from freshly killed processes,
    # then retry before falling back to the manual walk.
    time.sleep(1)
    try:
        shutil.rmtree(path, onerror=_clear_readonly)
    except OSError:
        pass

    if not path.exists():
        print(f"  [OK] Removed: {path}")
        return True

    print("  [*] Directory not empty, trying force removal...")
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            item = Path(root) / name
            try:
                item.chmod(0o777)
                item.unlink()
            except OSError as exc:
                write_log(f"Skip {item}: {exc}", "WARNING")
        for name in dirs:
            item = Path(root) / name
            try:
                item.rmdir()
            except OSError as exc:
                write_log(f"Skip {item}: {exc}", "WARNING")

    try:
        path.rmdir()
        print(f"  [OK] Force removed: {path}")
        return True
    except OSError as exc:
        write_log(f"Force removal failed: {exc}", "ERROR")
        print_color(f"  [!] Could not fully remove: {path}", Colors.YELLOW)
        return False

def reset_qoder_completely():
    """Reset Qoder completely with better error handling"""
    global QODER_DATA_DIR, QODER_USER_DIR
    
    print_color("\n[*] Resetting Qoder completely...", Colors.YELLOW)
    write_log("Starting complete Qoder reset", "INFO")
    
    # Kill Qoder process first (including the process tree so spawned
    # helper binaries cannot keep file handles open during removal).
    try:
        if IS_MAC:
            subprocess.run(["pkill", "-f", "Qoder"], capture_output=True)
        elif IS_WINDOWS:
            subprocess.run(["taskkill", "/F", "/T", "/IM", "Qoder.exe"], capture_output=True)
        elif IS_LINUX:
            subprocess.run(["pkill", "-f", "qoder"], capture_output=True)
        print("  [*] Killed Qoder processes")
        time.sleep(2)
    except Exception as e:
        write_log(f"Error killing Qoder: {e}", "WARNING")
    
    # Reset data directories
    success = True
    
    if QODER_DATA_DIR:
        # Try to remove specific problematic subdirectories first
        problematic_dirs = [
            QODER_DATA_DIR / "SharedClientCache",
            QODER_DATA_DIR / "Cache",
            QODER_DATA_DIR / "Code Cache",
        ]
        
        for dir_path in problematic_dirs:
            if dir_path.exists():
                force_remove_tree(dir_path)
        
        # Now remove the main directory; its removal is authoritative.
        if QODER_DATA_DIR.exists() and not force_remove_tree(QODER_DATA_DIR):
            success = False
    
    if QODER_USER_DIR and QODER_USER_DIR.exists():
        if not force_remove_tree(QODER_USER_DIR):
            success = False
    
    # Remove the separate cache location too, otherwise cached network and
    # app state survive a "complete" reset.
    if QODER_CACHE_DIR and QODER_CACHE_DIR.exists():
        if not force_remove_tree(QODER_CACHE_DIR):
            success = False
    
    # Recreate directories with fresh data
    if QODER_DATA_DIR:
        QODER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"  Ã¢Å“â€¦ Recreated: {QODER_DATA_DIR}")
    
    if QODER_USER_DIR:
        QODER_USER_DIR.mkdir(parents=True, exist_ok=True)
        print(f"  Ã¢Å“â€¦ Recreated: {QODER_USER_DIR}")
    
    # Re-apply patch
    patcher = QoderPatcher(SELECTED_PLATFORM)
    patcher.patch_qoder_data()
    
    if success:
        print_color("\n[OK] Qoder reset completed!", Colors.GREEN)
        write_log("Qoder reset completed", "SUCCESS")
    else:
        print_color("\n[!] Qoder reset finished with removal failures", Colors.YELLOW)
        write_log("Qoder reset completed with removal failures", "WARNING")
    return success

# ================= MAIN =================

async def process_all_client(headless: bool = True):
    """Process all accounts using Qoder Client"""
    accounts = load_accounts()
    if not accounts:
        print_color(f"[!] Tidak ada akun. Buat file {AKUN_FILE}", Colors.RED)
        print_color(f"Format: EMAIL|PASSWORD", Colors.YELLOW)
        return
    
    # Filter out already processed accounts
    processed_emails = load_processed_emails()
    accounts = [acc for acc in accounts if acc["email"] not in processed_emails]
    
    if not accounts:
        print_color("[!] Semua akun sudah diproses!", Colors.GREEN)
        return
    
    print(f"\n{Colors.CYAN}Ã°Å¸â€œâ€¹ {len(accounts)} akun tersisa untuk diproses{Colors.RESET}")
    
    success = 0
    failed = 0
    
    for i, acc in enumerate(accounts, 1):
        print(f"\n{Colors.CYAN}[{i}/{len(accounts)}] {acc['email']}{Colors.RESET}")
        
        bot = QoderClientAutomation(headless=headless, platform_type=SELECTED_PLATFORM)
        result = await bot.run_client_login(acc["email"], acc["password"])
        
        if result and result.get("success"):
            success += 1
        else:
            failed += 1
        
        if i < len(accounts):
            delay = random.randint(30, 60)
            print(f"\n  Ã¢ÂÂ³ Tunggu {delay}s...")
            write_log(f"Waiting {delay}s before next account", "INFO")
            await asyncio.sleep(delay)
    
    print_color(f"\nÃ¢Å“â€¦ {success} sukses, Ã¢ÂÅ’ {failed} gagal", Colors.GREEN if success > 0 else Colors.RED)

def select_platform():
    """Menu untuk memilih platform"""
    global SELECTED_PLATFORM
    print(f"""
{Colors.CYAN}Ã¢â€¢â€Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢â€”
Ã¢â€¢â€˜              PILIH PLATFORM                              Ã¢â€¢â€˜
Ã¢â€¢Â Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â£
Ã¢â€¢â€˜  {Colors.GREEN}1.  macOS (Default){Colors.WHITE}                           Ã¢â€¢â€˜
Ã¢â€¢â€˜  {Colors.BLUE}2.  Windows{Colors.WHITE}                                   Ã¢â€¢â€˜
Ã¢â€¢â€˜  {Colors.YELLOW}3.  Linux{Colors.WHITE}                                     Ã¢â€¢â€˜
Ã¢â€¢Å¡Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â{Colors.RESET}
""")
    
    choice = input(f"{Colors.YELLOW}Pilih platform (1-3): {Colors.RESET}").strip()
    
    if choice == "1":
        SELECTED_PLATFORM = "Darwin"
    elif choice == "2":
        SELECTED_PLATFORM = "Windows"
    elif choice == "3":
        SELECTED_PLATFORM = "Linux"
    else:
        print_color("[!] Pilihan tidak valid, menggunakan default", Colors.RED)
        SELECTED_PLATFORM = SYSTEM
    
    init_platform(SELECTED_PLATFORM)
    print_color(f"\nÃ¢Å“â€¦ Platform selected: {PLATFORM_NAME}", Colors.GREEN)
    return SELECTED_PLATFORM

async def main():
    """Main menu"""
    setup_logging()
    banner()
    
    # Platform selection
    select_platform()
    
    # Check Playwright browser on startup
    print_color("\n[Ã°Å¸â€Â§] Checking Playwright browser...", Colors.YELLOW)
    ensure_playwright_browsers()
    
    while True:
        print(f"""
{Colors.WHITE}Ã¢â€¢â€Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢â€”
Ã¢â€¢â€˜                 QODERPILOT MENU                         Ã¢â€¢â€˜
Ã¢â€¢Â Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â£
Ã¢â€¢â€˜  Platform: {Colors.CYAN}{PLATFORM_NAME}{Colors.WHITE}                              Ã¢â€¢â€˜
Ã¢â€¢Â Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â£
Ã¢â€¢â€˜  {Colors.CYAN}CLIENT LOGIN{Colors.WHITE}:                                      Ã¢â€¢â€˜
Ã¢â€¢â€˜  1.  Process All Accounts                               Ã¢â€¢â€˜
Ã¢â€¢â€˜  2.  Process Single Account                            Ã¢â€¢â€˜
Ã¢â€¢â€˜                                                          Ã¢â€¢â€˜
Ã¢â€¢â€˜  {Colors.CYAN}PATCH & RESET{Colors.WHITE}:                                   Ã¢â€¢â€˜
Ã¢â€¢â€˜  3.  Patch Qoder Data                                   Ã¢â€¢â€˜
Ã¢â€¢â€˜  4.  Reset Qoder Completely                             Ã¢â€¢â€˜
Ã¢â€¢â€˜  9.  Deep Reset (All Data)                             Ã¢â€¢â€˜
Ã¢â€¢â€˜                                                          Ã¢â€¢â€˜
Ã¢â€¢â€˜  {Colors.CYAN}PLATFORM{Colors.WHITE}:                                        Ã¢â€¢â€˜
Ã¢â€¢â€˜  5.  Change Platform                                    Ã¢â€¢â€˜
Ã¢â€¢â€˜                                                          Ã¢â€¢â€˜
Ã¢â€¢â€˜  {Colors.CYAN}UTILITY{Colors.WHITE}:                                      Ã¢â€¢â€˜
Ã¢â€¢â€˜  6.  View Results                                       Ã¢â€¢â€˜
Ã¢â€¢â€˜  7.  View Log                                           Ã¢â€¢â€˜
Ã¢â€¢â€˜  8.  Check Qoder Status                                 Ã¢â€¢â€˜
Ã¢â€¢â€˜  0.  Exit                                                Ã¢â€¢â€˜
Ã¢â€¢Å¡Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â{Colors.RESET}
""")
        choice = input(f"{Colors.YELLOW}Pilih (0-9): {Colors.RESET}").strip()
        
        if choice == "0":
            print_color("Ã°Å¸â€˜â€¹ Terima kasih!", Colors.GREEN)
            break
        elif choice == "1":
            await process_all_client(headless=True)
        elif choice == "2":
            email = input("  Email: ").strip()
            password = input("  Password: ").strip()
            if email and password:
                bot = QoderClientAutomation(headless=True, platform_type=SELECTED_PLATFORM)
                await bot.run_client_login(email, password)
        elif choice == "3":
            patcher = QoderPatcher(SELECTED_PLATFORM)
            patcher.patch_qoder_data()
        elif choice == "4":
            confirm = input("  Ã¢Å¡Â Ã¯Â¸Â Reset Qoder completely? (y/n): ").strip().lower()
            if confirm == 'y':
                reset_qoder_completely()
        elif choice == "5":
            select_platform()
        elif choice == "6":
            try:
                with open(SUCCESS_FILE, "r") as f:
                    lines = f.readlines()
                    if lines:
                        print(f"\n{Colors.CYAN}===== Results ====={Colors.RESET}")
                        for line in lines[-10:]:
                            parts = line.split('|')
                            if len(parts) >= 3:
                                email = parts[0]
                                data = json.loads(parts[1])
                                credits = data.get('credits', 0)
                                timestamp = parts[2].strip()
                                status = "Ã¢Å“â€¦" if credits >= 300 else "Ã¢Å¡Â Ã¯Â¸Â"
                                print(f"{status} {email} - {credits} credits ({timestamp})")
                    else:
                        print_color("Belum ada hasil", Colors.YELLOW)
            except FileNotFoundError:
                print_color("Belum ada hasil", Colors.YELLOW)
        elif choice == "7":
            try:
                with open(LOG_FILE, "r") as f:
                    lines = f.readlines()
                    if lines:
                        print(f"\n{Colors.CYAN}===== Last 20 Log Entries ====={Colors.RESET}")
                        for line in lines[-20:]:
                            print(line.strip())
                    else:
                        print_color("Log kosong", Colors.YELLOW)
            except FileNotFoundError:
                print_color("Log file belum ada", Colors.YELLOW)
        elif choice == "8":
            print_color(f"\n[Ã°Å¸â€Â] Qoder Status:", Colors.CYAN)
            print(f"  Platform: {PLATFORM_NAME}")
            print(f"  Binary path: {QODER_BINARY}")
            print(f"  Exists: {os.path.exists(QODER_BINARY) if QODER_BINARY else False}")
            print(f"  Data directory: {QODER_DATA_DIR}")
            print(f"  Exists: {QODER_DATA_DIR.exists() if QODER_DATA_DIR else False}")
            print(f"  User directory: {QODER_USER_DIR}")
            print(f"  Exists: {QODER_USER_DIR.exists() if QODER_USER_DIR else False}")
        elif choice == "9":
            confirm = input("  Ã¢Å¡Â Ã¯Â¸Â Deep Reset - Menghapus SEMUA data Qoder? (y/n): ").strip().lower()
            if confirm == 'y':
                reset_qoder_deep()
        else:
            print_color("[!] Pilihan tidak valid", Colors.RED)

if __name__ == "__main__":
    asyncio.run(main())
