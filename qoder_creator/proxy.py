"""
QoderPilot - Proxy Manager
Rotating proxy pool dengan format: http://user:pass@host:port atau host:port:user:pass
"""

import os
import random
import re
from typing import Optional, Dict, List
from urllib.parse import quote, urlparse

from .utils import write_log


_PROXY_TUNNEL_CODE_RE = re.compile(r"tunnel connection failed:\s*(\d{3})", re.IGNORECASE)


def proxy_error_hint(exc: BaseException) -> Optional[str]:
    """Diagnose HTTP-proxy tunnel rejections surfaced by urllib.

    Returns a human-readable hint when the exception shows that the proxy
    itself refused the CONNECT tunnel (e.g. 402 balance exhausted, 407 bad
    credentials); otherwise returns None so callers can keep the raw error.
    """
    reason = getattr(exc, "reason", None)
    text = str(reason if reason is not None else exc)
    match = _PROXY_TUNNEL_CODE_RE.search(text)
    if not match:
        return None

    code = int(match.group(1))
    if code == 402:
        return (
            "Proxy rejected the CONNECT tunnel with HTTP 402 Payment Required; "
            "the proxy balance/quota is likely exhausted. Top up the proxy "
            "subscription or replace proxies.txt with a working proxy"
        )
    if code == 407:
        return (
            "Proxy rejected the CONNECT tunnel with HTTP 407 Proxy Authentication "
            "Required; check the username/password in proxies.txt"
        )
    return (
        f"Proxy rejected the CONNECT tunnel with HTTP {code}; "
        "check the proxy provider account/status"
    )


def proxy_url(proxy: Dict[str, str]) -> str:
    """Build an authenticated proxy URL from Playwright proxy settings."""
    server = proxy.get("server", "")
    username = proxy.get("username", "")
    if not server or not username:
        return server

    parsed = urlparse(server)
    password = quote(proxy.get("password", ""), safe="")
    user = quote(username, safe="")
    host = parsed.hostname or ""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    port = f":{parsed.port}" if parsed.port else ""
    return parsed._replace(netloc=f"{user}:{password}@{host}{port}").geturl()


class ProxyPool:
    """Rotating proxy pool manager."""

    def __init__(self, proxies: List[str] = None, pool_path: str = None):
        self._proxies: List[str] = []
        self._idx = 0

        if proxies:
            self._proxies = proxies
        elif pool_path and os.path.exists(pool_path):
            self.load(pool_path)

    def load(self, path: str):
        """Load proxies from file (one per line)."""
        with open(path, "r") as f:
            self._proxies = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
        write_log(f"Loaded {len(self._proxies)} proxies from {path}", "INFO")

    @property
    def count(self) -> int:
        return len(self._proxies)

    def next(self) -> Optional[Dict[str, str]]:
        """Get next proxy in round-robin. Returns {server, username, password} or None."""
        if not self._proxies:
            return None

        raw = self._proxies[self._idx % len(self._proxies)]
        self._idx += 1
        return self._parse(raw)

    def random(self) -> Optional[Dict[str, str]]:
        """Get a random proxy."""
        if not self._proxies:
            return None
        return self._parse(random.choice(self._proxies))

    @staticmethod
    def _parse(raw: str) -> Dict[str, str]:
        """Parse proxy string into structured dict."""
        # Format: http://user:pass@host:port
        if raw.startswith("http"):
            u = urlparse(raw)
            return {
                "server": f"{u.scheme}://{u.hostname}:{u.port}",
                "username": u.username or "",
                "password": u.password or "",
            }

        # Format: host:port:user:pass
        parts = raw.split(":")
        if len(parts) == 4:
            return {
                "server": f"http://{parts[0]}:{parts[1]}",
                "username": parts[2],
                "password": parts[3],
            }

        # Format: host:port
        if len(parts) == 2:
            return {"server": f"http://{parts[0]}:{parts[1]}"}

        raise ValueError(f"Invalid proxy format: {raw[:30]}...")
