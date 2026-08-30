"""
QoderPilot - Utilities
Logging, random generators, save/load helpers.
"""

import json
import random
import string
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .config import LOG_FILE, DATA_DIR


# ================= LOGGING =================
def setup_logging():
    """Setup logging - create log file if not exists."""
    if not LOG_FILE.exists():
        LOG_FILE.write_text(
            f"# QoderPilot Log - {datetime.now(timezone.utc).isoformat()}\n"
        )


def write_log(message: str, level: str = "INFO"):
    """Write a log entry."""
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")


# ================= JSONL =================
def save_jsonl(filepath: Path, data: Dict[str, Any]):
    """Append a JSON line to a file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def load_jsonl(filepath: Path) -> list:
    """Load all lines from a JSONL file."""
    if not filepath.exists():
        return []
    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return results


# ================= GENERATORS =================
_SECURE_RANDOM = random.SystemRandom()

def generate_password(length: int = 14) -> str:
    """Generate a password that always satisfies Qoder's signup policy:
    8-20 characters with at least one uppercase, one lowercase, and one digit.

    Only alphanumerics are used; symbols are avoided because Qoder's form
    validates "upper and lower case letters and numbers".
    """
    length = max(8, min(20, length))
    chars = string.ascii_letters + string.digits
    # Guarantee at least one character from each required class.
    password = [
        _SECURE_RANDOM.choice(string.ascii_uppercase),
        _SECURE_RANDOM.choice(string.ascii_lowercase),
        _SECURE_RANDOM.choice(string.digits),
    ]
    password.extend(_SECURE_RANDOM.choice(chars) for _ in range(length - len(password)))
    _SECURE_RANDOM.shuffle(password)
    return "".join(password)


def generate_machine_id() -> str:
    """Generate a fake machine ID (UUID v4, matches Qoder's native format)."""
    return str(uuid.uuid4())


def generate_ms_deviceid() -> str:
    """Generate a fake Microsoft device ID."""
    return str(uuid.uuid4())


def generate_nonce(length: int = 16) -> str:
    """Generate a random nonce."""
    return uuid.uuid4().hex[:length]


# ================= TEXT HELPERS =================
def extract_otp(text: str, length: int = 6) -> Optional[str]:
    """Extract OTP/verification code from text."""
    import re
    patterns = [
        rf'\b(\d{{{length}}})\b',
        r'verification code[:\s]+(\d{4,8})',
        r'code[:\s]+(\d{4,8})',
        r'OTP[:\s]+(\d{4,8})',
        r'one.time.passcode[:\s]+(\d{4,8})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None
