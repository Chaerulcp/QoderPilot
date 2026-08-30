"""Configuration for the self-contained Qoder pipeline."""

from __future__ import annotations

import os
try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when config.toml contains an invalid value."""


@dataclass(frozen=True)
class PipelineConfig:
    config_path: Path
    project_root: Path
    data_dir: Path
    tempmail_base: str
    proxy_mode: str
    proxy_file: Path
    signup_headless: bool
    client_headless: bool
    platform: str
    default_count: int
    delay_min_seconds: int
    delay_max_seconds: int

    @property
    def pending_file(self) -> Path:
        return self.data_dir / "pending_jobs.jsonl"

    @property
    def success_file(self) -> Path:
        return self.data_dir / "qoder_sukses.txt"

    @property
    def failed_file(self) -> Path:
        return self.data_dir / "qoder_failed.txt"

    @property
    def client_log_file(self) -> Path:
        return self.data_dir / "qoder_client.log"


def _section(raw: dict[str, Any], name: str) -> dict[str, Any]:
    value = raw.get(name, {})
    if not isinstance(value, dict):
        raise ConfigError(f"Bagian [{name}] harus berupa tabel TOML.")
    return value


def _boolean(section: dict[str, Any], key: str, default: bool) -> bool:
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"'{key}' harus true atau false.")
    return value


def _integer(section: dict[str, Any], key: str, default: int) -> int:
    value = section.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"'{key}' harus berupa integer.")
    return value


def _local_path(root: Path, raw: Any, default: str) -> Path:
    value = raw if isinstance(raw, str) and raw.strip() else default
    path = Path(os.path.expandvars(value)).expanduser()
    return path if path.is_absolute() else (root / path).resolve()


def load_config(path: Path) -> PipelineConfig:
    config_path = path.expanduser().resolve()
    if not config_path.is_file():
        raise ConfigError(f"File konfigurasi tidak ditemukan: {config_path}")
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    root = config_path.parent
    api = _section(raw, "api")
    signup = _section(raw, "signup")
    proxy = _section(raw, "proxy")
    output = _section(raw, "output")
    client = _section(raw, "client")
    pipeline = _section(raw, "pipeline")

    proxy_mode = str(proxy.get("mode", "none")).lower()
    if proxy_mode not in {"none", "file", "env"}:
        raise ConfigError("proxy.mode harus none, file, atau env.")
    platform = str(client.get("platform", "Windows"))
    if platform not in {"Windows", "Darwin", "Linux"}:
        raise ConfigError("client.platform harus Windows, Darwin, atau Linux.")

    count = _integer(pipeline, "default_count", 1)
    delay_min = _integer(client, "delay_min_seconds", 30)
    delay_max = _integer(client, "delay_max_seconds", 60)
    if count < 1:
        raise ConfigError("pipeline.default_count minimal 1.")
    if delay_min < 0 or delay_max < delay_min:
        raise ConfigError("Rentang delay client tidak valid.")

    tempmail_base = str(api.get("tempmail_base", "")).strip()
    return PipelineConfig(
        config_path=config_path,
        project_root=root,
        data_dir=_local_path(root, output.get("data_dir"), "data"),
        tempmail_base=tempmail_base,
        proxy_mode=proxy_mode,
        proxy_file=_local_path(root, proxy.get("pool_file"), "proxies.txt"),
        signup_headless=_boolean(signup, "headless", True),
        client_headless=_boolean(client, "headless", False),
        platform=platform,
        default_count=count,
        delay_min_seconds=delay_min,
        delay_max_seconds=delay_max,
    )



