"""
QoderPilot - Tempik API Client
Self-hosted temp mail service: https://github.com/hirotomasato/tempik

Endpoints:
  GET  /api/session               â†’ { sessionId }
  POST /api/inboxes                â†’ { address, created_at }
  GET  /api/inboxes/{addr}/messages â†’ [ { subject, body, from_address, received_at } ]
"""

import asyncio
import json
import random
import re
import time
from datetime import datetime
from urllib.error import HTTPError, URLError
import urllib.request
from typing import List, Optional, Dict, Any

from .config import TEMPIK_BASE
from .proxy import proxy_error_hint, proxy_url
from .utils import write_log

# Browser-like User-Agent to bypass Cloudflare
_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/132.0.0.0 Safari/537.36"
)


class TempMailError(RuntimeError):
    """Raised when the configured temporary-mail API cannot be used."""


class TempikClient:
    """Tempik disposable email API client."""

    def __init__(self, base_url: str = None, proxy: Dict[str, str] = None):
        self.base_url = (base_url or TEMPIK_BASE).rstrip("/")
        self.session_id: Optional[str] = None
        self._email: Optional[str] = None
        self._domains: List[str] = []
        self._opener = urllib.request.build_opener()
        if proxy:
            url = proxy_url(proxy)
            self._opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": url, "https": url})
            )

    # ==================== CONFIG ====================
    def _fetch_domains(self) -> List[str]:
        """Fetch available domains from /api/config. Cached."""
        if self._domains:
            return self._domains
        try:
            url = f"{self.base_url}/config"
            req = urllib.request.Request(url, method="GET")
            req.add_header("Accept", "application/json")
            req.add_header("User-Agent", _BROWSER_UA)
            with self._opener.open(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            self._domains = data.get("mailDomains", [data.get("mailDomain", "exse7en.fr")])
            write_log(f"Tempik domains: {self._domains}", "INFO")
        except Exception as e:
            write_log(f"Tempik domain fetch failed: {e}, using default", "WARNING")
            self._domains = ["exse7en.fr"]
        return self._domains

    # ==================== SESSION ====================
    def init_session(self) -> str:
        """Create a new session. Returns sessionId."""
        if self.session_id:
            return self.session_id

        url = f"{self.base_url}/session"
        req = urllib.request.Request(url, method="GET")
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", _BROWSER_UA)
        req.add_header("Accept-Language", "en-US,en;q=0.9")

        try:
            with self._opener.open(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except HTTPError as exc:
            hint = " Check that `api.tempmail_base` includes the API path (usually `/api`)." if exc.code == 404 else ""
            raise TempMailError(
                f"Temp mail session request failed ({exc.code} {exc.reason}) at {url}.{hint}"
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            hint = proxy_error_hint(exc)
            message = f"Unable to start a temp mail session at {url}: {exc}"
            if hint:
                message = f"{message} ({hint})"
            raise TempMailError(message) from exc

        self.session_id = data.get("sessionId") or data.get("id") or data.get("session_id")
        if not self.session_id:
            raise TempMailError(f"Temp mail session response from {url} did not include a session ID")
        write_log(f"Tempik session: {self.session_id[:8]}...", "INFO")
        return self.session_id

    # ==================== INBOX ====================
    def create_inbox(self, local_part: str = None, domain: str = None) -> str:
        """Create a new inbox. Returns email address.

        If domain is not specified, picks a random domain from available domains.
        """
        self.init_session()

        # Pick random domain if not specified
        if not domain:
            domains = self._fetch_domains()
            domain = random.choice(domains)

        url = f"{self.base_url}/inboxes"
        body_data = {"domain": domain}
        if local_part:
            body_data["localPart"] = local_part
        body = json.dumps(body_data).encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-session-id", self.session_id)
        req.add_header("User-Agent", _BROWSER_UA)
        req.add_header("Accept-Language", "en-US,en;q=0.9")

        try:
            with self._opener.open(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except HTTPError as exc:
            raise TempMailError(
                f"Temp mail inbox request failed ({exc.code} {exc.reason}) at {url}"
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            hint = proxy_error_hint(exc)
            message = f"Unable to create a temp mail inbox at {url}: {exc}"
            if hint:
                message = f"{message} ({hint})"
            raise TempMailError(message) from exc

        self._email = data.get("address")
        if not self._email:
            raise TempMailError(f"Temp mail inbox response from {url} did not include an address")
        write_log(f"Tempik inbox: {self._email} (domain={domain})", "INFO")
        return self._email

    # ==================== MESSAGES ====================
    def get_messages(self, address: str = None) -> List[Dict[str, Any]]:
        """Get all messages for an inbox address."""
        addr = address or self._email
        if not addr:
            raise ValueError("No email address provided")

        url = f"{self.base_url}/inboxes/{addr}/messages"
        req = urllib.request.Request(url, method="GET")
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", _BROWSER_UA)
        if self.session_id:
            req.add_header("x-session-id", self.session_id)

        with self._opener.open(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        return data if isinstance(data, list) else []

    async def wait_for_messages(
        self,
        address: str = None,
        max_wait: int = 150,
        interval: int = 5,
    ) -> List[Dict[str, Any]]:
        """Poll for messages until one arrives or timeout."""
        addr = address or self._email
        t0 = time.time()
        next_progress_log = 30

        while time.time() - t0 < max_wait:
            try:
                messages = self.get_messages(addr)
                if messages and len(messages) > 0:
                    write_log(f"Tempik received {len(messages)} message(s) for {addr}", "SUCCESS")
                    return messages
            except Exception as e:
                write_log(f"Tempik poll error: {e}", "WARNING")

            elapsed = int(time.time() - t0)
            if elapsed >= next_progress_log:
                write_log(f"Tempik inbox still empty for {addr} after {elapsed}s", "INFO")
                next_progress_log += 30
            await asyncio.sleep(interval)

        write_log(f"Tempik inbox timeout for {addr} after {max_wait}s", "WARNING")
        return []

    # ==================== OTP ====================
    @staticmethod
    def _message_stamp(msg: Dict[str, Any]) -> Optional[float]:
        """Parse a message timestamp into epoch seconds, or None."""
        raw = msg.get("received_at")
        if isinstance(raw, (int, float)):
            return float(raw)
        if not isinstance(raw, str) or not raw.strip():
            return None
        text = raw.strip()
        try:
            return float(text)
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None

    @classmethod
    def _latest_first(cls, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order messages newest-first so a resent code wins over a stale one."""
        stamps = [cls._message_stamp(msg) for msg in messages]
        if not any(stamp is not None for stamp in stamps):
            return list(messages)
        filled = [stamp if stamp is not None else 0.0 for stamp in stamps]
        order = sorted(range(len(messages)), key=lambda i: (filled[i], i), reverse=True)
        return [messages[i] for i in order]

    def extract_otp(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Extract verification code from messages.

        Qoder sends HTML email with the code as a standalone 6-digit number
        after "Verify your email" text. We strip HTML tags first, then search
        for the code in the plain text. Messages are scanned newest-first so a
        resent code takes precedence over an earlier, possibly expired, one.
        """
        for msg in self._latest_first(messages):
            subject = msg.get("subject", "")
            body = msg.get("body", "") or msg.get("text", "") or ""

            # Strip HTML tags to get plain text
            plain = re.sub(r"<[^>]+>", " ", body)
            plain = re.sub(r"\s+", " ", plain).strip()
            content = f"{subject} {plain}"

            write_log(f"OTP plain text: {content[:300]}", "INFO")

            patterns = [
                # Qoder specific: "Verify your email" OR "start using Qoder"
                # followed by a standalone 6-digit code
                r"(?:verify\s+your\s+email|start\s+using\s+Qoder)[\s\S]*?(\d{6})",
                # Generic fallback: standalone 6-digit code
                r"\b(\d{6})\b",
                # Other formats
                r"verification\s*code\s*:?\s*(\d{4,8})",
                r"code\s*:?\s*(\d{4,8})",
                r"OTP\s*:?\s*(\d{4,8})",
                r"passcode\s*:?\s*(\d{4,8})",
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    code = match.group(1)
                    write_log(f"OTP extracted: {code}", "SUCCESS")
                    return code

        return None

    async def wait_for_otp(
        self,
        address: str = None,
        max_wait: int = 150,
        interval: int = 5,
    ) -> Optional[str]:
        """Wait for OTP email and extract the code."""
        messages = await self.wait_for_messages(address, max_wait, interval)
        if messages:
            return self.extract_otp(messages)
        return None

    @property
    def email(self) -> Optional[str]:
        return self._email
