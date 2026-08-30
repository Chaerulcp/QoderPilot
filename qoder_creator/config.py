"""
QoderPilot - Configuration
Semua config dari config.toml (fallback ke env vars + defaults).
"""

import os
import platform
try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path
from typing import Any


# ================= LOAD CONFIG.TOML =================
_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.toml"
_CONFIG_PATH = Path(os.getenv("QODER_CONFIG", str(_DEFAULT_CONFIG_PATH))).resolve()


def _load_toml() -> dict:
    """Load the selected TOML configuration."""
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    return {}


_CONFIG = _load_toml()


def _cfg(*keys: str, default: Any = None) -> Any:
    """Get nested config value: _cfg('api', 'twocaptcha_key')"""
    val = _CONFIG
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            return default
    return val if val is not None else default


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


# ================= PLATFORM =================
SYSTEM = platform.system()
IS_MAC = SYSTEM == "Darwin"
IS_WINDOWS = SYSTEM == "Windows"
IS_LINUX = SYSTEM == "Linux"

# ================= API URLs =================
TEMPIK_BASE = os.getenv("TEMPIK_BASE", _cfg("api", "tempmail_base", default="https://tempik.example.com/api"))
QODER_BASE = _cfg("api", "qoder_base", default="https://qoder.com")
QODER_OPENAPI = _cfg("api", "qoder_openapi", default="https://openapi.qoder.sh")

# ================= SIGNUP =================
HEADLESS = _cfg("signup", "headless", default=True)
SIGNUP_DELAY = _cfg("signup", "delay", default=5)
SIGNUP_RETRY = _cfg("signup", "retry", default=2)
CONCURRENCY = _cfg("signup", "concurrency", default=1)

# ================= PROXY =================
PROXY_MODE = _cfg("proxy", "mode", default="none")  # "none" | "file" | "env"

# ================= FILE PATHS =================
BASE_DIR = _CONFIG_PATH.parent
PROXY_FILE = Path(_cfg("proxy", "pool_file", default="proxies.txt"))
if not PROXY_FILE.is_absolute():
    PROXY_FILE = BASE_DIR / PROXY_FILE
DATA_DIR = Path(_cfg("output", "data_dir", default="data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = BASE_DIR / DATA_DIR

ACCOUNTS_FILE = DATA_DIR / "accounts.jsonl"
LOG_FILE = Path(_cfg("logging", "file", default="data/qoder.log"))
if not LOG_FILE.is_absolute():
    LOG_FILE = BASE_DIR / LOG_FILE

# ================= DEFAULTS =================
DEFAULT_PASSWORD_LENGTH = 14
DEFAULT_TIMEOUT = 120000
DEFAULT_OTP_TIMEOUT = 150

# Ensure data dir exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Ensure log dir exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def show_config():
    """Print current configuration (hide sensitive)."""
    print_color(f"\n{'='*50}", Colors.CYAN)
    print_color("CONFIGURATION", Colors.BOLD)
    print_color(f"{'='*50}", Colors.CYAN)
    print(f"  Tempik API  : {TEMPIK_BASE}")
    print(f"  Qoder API   : {QODER_OPENAPI}")
    print(f"  Proxy Mode  : {PROXY_MODE}")
    print(f"  Headless    : {HEADLESS}")
    print(f"  Concurrency : {CONCURRENCY}")
    print(f"  Data Dir    : {DATA_DIR}")
    print(f"  Log File    : {LOG_FILE}")
