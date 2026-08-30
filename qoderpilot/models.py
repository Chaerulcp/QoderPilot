"""Domain models for account jobs and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

ProxySettings = dict[str, str]


@dataclass(frozen=True)
class PendingJob:
    email: str
    password: str
    proxy: Optional[ProxySettings]
    created_at: str

    @classmethod
    def create(
        cls, email: str, password: str, proxy: Optional[ProxySettings]
    ) -> "PendingJob":
        if not email or "@" not in email or not password:
            raise ValueError("Hasil signup tidak memiliki email/password yang valid.")
        return cls(
            email=email,
            password=password,
            proxy=dict(proxy) if proxy else None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PendingJob":
        email = value.get("email")
        password = value.get("password")
        proxy = value.get("proxy")
        created_at = value.get("created_at", "")
        if not isinstance(email, str) or "@" not in email:
            raise ValueError("Email pending tidak valid.")
        if not isinstance(password, str) or not password:
            raise ValueError("Password pending tidak valid.")
        if proxy is not None and not isinstance(proxy, dict):
            raise ValueError("Proxy pending tidak valid.")
        normalized_proxy = None
        if proxy:
            normalized_proxy = {str(key): str(item) for key, item in proxy.items()}
        return cls(email, password, normalized_proxy, str(created_at))

    def as_dict(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "password": self.password,
            "proxy": self.proxy,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class DoctorCheck:
    label: str
    ok: bool
    detail: str
    required: bool = True


@dataclass(frozen=True)
class PipelineStatus:
    pending: int
    successful: int
    failed: int


@dataclass(frozen=True)
class PipelineResult:
    exit_code: int
    message: str



