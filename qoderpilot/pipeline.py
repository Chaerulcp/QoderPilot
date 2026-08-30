"""Self-contained application service for signup followed by client login."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import random
import sys
from pathlib import Path
from typing import Any, Optional

from .config import PipelineConfig
from .models import DoctorCheck, PendingJob, PipelineResult, PipelineStatus, ProxySettings
from .storage import PendingJobStore, count_nonempty_lines


class PipelineError(RuntimeError):
    """Raised when the pipeline cannot safely start or continue."""


class QoderPilot:
    def __init__(self, config: PipelineConfig):
        self.config = config
        os.environ["QODER_CONFIG"] = str(config.config_path)
        self.pending = PendingJobStore(config.pending_file)
        self._proxy_pool: Any = None
        self._client_module: Any = None
        self._login_target: Optional[str] = None
        self._no_reset = False

    async def run(self, count: int, dry_run: bool = False, no_reset: bool = False) -> PipelineResult:
        if count < 1:
            raise ValueError("Jumlah akun minimal 1.")
        self._require_ready()
        if dry_run:
            proxy = self._next_proxy()
            return PipelineResult(0, self._dry_run_message(count, proxy))

        self._no_reset = no_reset
        self._prepare_runtime()
        signup_manager = self._create_signup_manager()
        created = client_ok = signup_failed = client_failed = 0
        for index in range(1, count + 1):
            proxy = self._next_proxy()
            self._announce_job(index, count, proxy)
            account = await signup_manager.create_account(index, proxy=proxy)
            if not account:
                signup_failed += 1
            else:
                created += 1
                job = PendingJob.create(account["email"], account["password"], proxy)
                self.pending.upsert(job)
                if await self._login_job(job):
                    client_ok += 1
                else:
                    client_failed += 1
            await self._delay_between_jobs(index, count)

        failures = signup_failed + client_failed
        message = (
            f"Pipeline selesai: {created} akun dibuat, {client_ok} login client berhasil, "
            f"{signup_failed} signup gagal, {client_failed} login tertunda."
        )
        return PipelineResult(0 if failures == 0 else 2, message)

    async def resume(self, no_reset: bool = False) -> PipelineResult:
        self._require_ready()
        jobs = self.pending.read()
        if not jobs:
            return PipelineResult(0, "Tidak ada akun pending.")
        self._no_reset = no_reset
        self._prepare_runtime()

        successful = failed = 0
        for index, job in enumerate(jobs, 1):
            self._announce_job(index, len(jobs), job.proxy, prefix="RESUME")
            if await self._login_job(job):
                successful += 1
            else:
                failed += 1
            await self._delay_between_jobs(index, len(jobs))
        return PipelineResult(
            0 if failed == 0 else 2,
            f"Resume selesai: {successful} berhasil, {failed} masih pending.",
        )

    def status(self) -> PipelineStatus:
        return PipelineStatus(
            pending=len(self.pending.read()),
            successful=count_nonempty_lines(self.config.success_file),
            failed=count_nonempty_lines(self.config.failed_file),
        )

    def doctor(self) -> list[DoctorCheck]:
        checks = [
            self._python_check(),
            self._local_source_check(),
            self._dependency_check(),
            self._tempmail_check(),
            self._proxy_check(),
            self._qoder_check(),
            self._chrome_check(),
            self._chromium_check(),
        ]
        return checks

    def patch_client(self, target: str = "ide") -> bool:
        self._require_ready()
        return self._patch_target(target)

    def reset_client(self, deep: bool = False, target: str = "ide") -> bool:
        self._require_ready()
        return self._reset_target(target, deep=deep)

    def _patch_target(self, target: str) -> bool:
        if target == "agentic":
            self._require_agentic_platform()
            self._prepare_client_module()
            from qoder_client.agentic import patch_agentic

            return bool(patch_agentic())
        module = self._prepare_client_module()
        patcher = module.QoderPatcher(self.config.platform)
        return bool(patcher.patch_qoder_data())

    def _reset_target(self, target: str, deep: bool = False) -> bool:
        if target == "agentic":
            self._require_agentic_platform()
            self._prepare_client_module()
            from qoder_client import agentic

            reset = agentic.reset_agentic_deep if deep else agentic.reset_agentic_completely
            return bool(reset())
        module = self._prepare_client_module()
        reset = module.reset_qoder_deep if deep else module.reset_qoder_completely
        return bool(reset())

    def _require_agentic_platform(self) -> None:
        if self.config.platform != "Windows":
            raise PipelineError("Qoder Agentic saat ini hanya didukung di Windows.")

    async def _login_job(self, job: PendingJob) -> bool:
        target = self._login_target or self._select_login_target()
        self._login_target = target
        if not self._prepare_target_for_login(target):
            return False
        automation = self._create_client_automation(job.proxy, target)
        try:
            result = await automation.run_client_login(job.email, job.password)
        except Exception as exc:
            self._write_client_error(job.email, exc)
            return False
        if not result or not result.get("success"):
            return False
        self.pending.remove(job.email)
        return True

    def _create_signup_manager(self) -> Any:
        from qoder_creator.signup import SignupManager

        return SignupManager(proxy_pool=None, headless=self.config.signup_headless)

    def _prepare_target_for_login(self, target: str) -> bool:
        if self._no_reset:
            return True
        label = "Qoder Agentic" if target == "agentic" else "Qoder IDE"
        print(f"[*] Reset {label} sebelum login...")
        if self._reset_target(target):
            return True
        message = f"Reset {label} gagal; login dilewati agar identitas tetap bersih."
        print(f"[!] {message}")
        self._write_client_error_line(message)
        return False

    def _write_client_error_line(self, message: str) -> None:
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        with self.config.client_log_file.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")

    def _create_client_automation(
        self,
        proxy: Optional[ProxySettings],
        target: str = "ide",
    ) -> Any:
        if target == "agentic":
            self._require_agentic_platform()
            from qoder_client.agentic import QoderAgenticAutomation

            return QoderAgenticAutomation(
                headless=self.config.client_headless,
                proxy=proxy,
            )

        module = self._prepare_client_module()
        return module.QoderClientAutomation(
            headless=self.config.client_headless,
            platform_type=self.config.platform,
            proxy=proxy,
        )

    @staticmethod
    def _select_login_target() -> str:
        """Ask once which installed Qoder application should receive the account."""
        print("\nPilih aplikasi tujuan login:")
        print("  1. Qoder IDE")
        print(r"  2. Qoder Agentic (C:\ProgramData\Qoder\Qoder Launcher)")
        while True:
            try:
                choice = input("Masukkan pilihan [1/2], lalu tekan Enter: ").strip()
            except EOFError as exc:
                raise PipelineError(
                    "Pemilihan aplikasi membutuhkan terminal interaktif."
                ) from exc
            if choice == "1":
                print("Target login: Qoder IDE")
                return "ide"
            if choice == "2":
                print("Target login: Qoder Agentic")
                return "agentic"
            print("Pilihan tidak valid. Masukkan angka 1 atau 2.")

    def _prepare_runtime(self) -> None:
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        from qoder_creator.utils import setup_logging

        setup_logging()
        self._prepare_client_module()

    def _prepare_client_module(self) -> Any:
        if self._client_module is not None:
            return self._client_module
        from qoder_client import automation

        automation.SUCCESS_FILE = str(self.config.success_file)
        automation.FAILED_FILE = str(self.config.failed_file)
        automation.LOG_FILE = str(self.config.client_log_file)
        automation.API_KEY_FILE = str(self.config.data_dir / "qoder_api_keys.txt")
        automation.AKUN_FILE = str(self.config.data_dir / "legacy_accounts.txt")
        automation.remove_account = lambda _email: None
        automation.setup_logging()
        automation.SELECTED_PLATFORM = self.config.platform
        automation.init_platform(self.config.platform)
        self._client_module = automation
        return automation

    def _next_proxy(self) -> Optional[ProxySettings]:
        if self.config.proxy_mode == "none":
            return None
        if self._proxy_pool is None:
            self._proxy_pool = self._create_proxy_pool()
        proxy = self._proxy_pool.next()
        if not proxy:
            raise PipelineError("Proxy pool kosong.")
        return proxy

    def _create_proxy_pool(self) -> Any:
        from qoder_creator.proxy import ProxyPool

        if self.config.proxy_mode == "env":
            value = os.getenv("QODER_PROXY", "").strip()
            return ProxyPool(proxies=[value] if value else [])
        return ProxyPool(pool_path=str(self.config.proxy_file))

    async def _delay_between_jobs(self, index: int, total: int) -> None:
        if index >= total:
            return
        delay = random.randint(
            self.config.delay_min_seconds,
            self.config.delay_max_seconds,
        )
        if delay:
            print(f"Menunggu {delay} detik sebelum job berikutnya...")
            await asyncio.sleep(delay)

    def _require_ready(self) -> None:
        failures = [item for item in self.doctor() if item.required and not item.ok]
        if not failures:
            return
        detail = "; ".join(f"{item.label}: {item.detail}" for item in failures)
        raise PipelineError(f"Pemeriksaan prasyarat gagal. {detail}")

    def _dependency_check(self) -> DoctorCheck:
        modules = ["playwright", "rich", "playwright_stealth", "pyautogui"]
        missing = [name for name in modules if importlib.util.find_spec(name) is None]
        if missing:
            return DoctorCheck("Dependensi", False, f"Belum terpasang: {', '.join(missing)}")
        return DoctorCheck("Dependensi", True, "Semua modul runtime utama tersedia.")

    def _proxy_check(self) -> DoctorCheck:
        if self.config.proxy_mode == "none":
            return DoctorCheck("Proxy", True, "Dinonaktifkan (kedua tahap direct).")
        if self.config.proxy_mode == "env":
            present = bool(os.getenv("QODER_PROXY", "").strip())
            return DoctorCheck("Proxy", present, "QODER_PROXY tersedia." if present else "QODER_PROXY kosong.")
        if not self.config.proxy_file.is_file():
            return DoctorCheck("Proxy", False, f"File tidak ditemukan: {self.config.proxy_file}")
        try:
            pool = self._create_proxy_pool()
        except (OSError, ValueError) as exc:
            return DoctorCheck("Proxy", False, str(exc))
        return DoctorCheck("Proxy", pool.count > 0, f"{pool.count} proxy lokal tersedia.")

    def _local_source_check(self) -> DoctorCheck:
        required = [
            self.config.project_root / "qoder_creator" / "signup.py",
            self.config.project_root / "qoder_client" / "automation.py",
            self.config.project_root / "qoder_client" / "agentic.py",
            self.config.project_root / "qoder_client" / "proxy_bridge.py",
        ]
        missing = [str(path) for path in required if not path.is_file()]
        detail = "Source lokal lengkap." if not missing else f"Hilang: {', '.join(missing)}"
        return DoctorCheck("Source mandiri", not missing, detail)

    def _tempmail_check(self) -> DoctorCheck:
        valid = bool(self.config.tempmail_base) and "example.com" not in self.config.tempmail_base
        detail = "Endpoint Temp Mail dikonfigurasi." if valid else "api.tempmail_base belum valid."
        return DoctorCheck("Temp Mail", valid, detail)

    @staticmethod
    def _python_check() -> DoctorCheck:
        ok = sys.version_info >= (3, 10)
        return DoctorCheck("Python", ok, sys.version.split()[0])

    def _qoder_check(self) -> DoctorCheck:
        if self.config.platform == "Windows":
            candidates = [
                Path("C:/Program Files/Qoder/Qoder.exe"),
                Path(os.getenv("LOCALAPPDATA", "")) / "Qoder" / "Qoder.exe",
                Path("C:/ProgramData/Qoder/Qoder Launcher/Qoder Launcher.exe"),
            ]
        elif self.config.platform == "Darwin":
            candidates = [Path("/Applications/Qoder.app")]
        else:
            candidates = [Path("/usr/bin/qoder"), Path("/usr/local/bin/qoder")]
        found = next((path for path in candidates if path.exists()), None)
        detail = str(found) if found else "IDE maupun Agentic Launcher tidak ditemukan."
        return DoctorCheck("Aplikasi Qoder", found is not None, detail)

    @staticmethod
    def _chrome_check() -> DoctorCheck:
        candidates = [
            Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
            Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
        found = next((path for path in candidates if path.exists()), None)
        return DoctorCheck("Google Chrome", found is not None, str(found or "Tidak ditemukan."))

    @staticmethod
    def _chromium_check() -> DoctorCheck:
        roots = [
            Path(os.getenv("LOCALAPPDATA", "")) / "ms-playwright",
            Path.home() / ".cache" / "ms-playwright",
            Path.home() / "Library" / "Caches" / "ms-playwright",
        ]
        found = next(
            (item for root in roots if root.is_dir() for item in root.glob("chromium-*") if item.is_dir()),
            None,
        )
        detail = str(found) if found else "Jalankan: python -m playwright install chromium"
        return DoctorCheck("Playwright Chromium", found is not None, detail)

    @staticmethod
    def _announce_job(
        index: int,
        total: int,
        proxy: Optional[ProxySettings],
        prefix: str = "RUN",
    ) -> None:
        server = proxy.get("server", "direct") if proxy else "direct"
        print(f"\n[{prefix} {index}/{total}] Proxy bersama: {server}")

    @staticmethod
    def _dry_run_message(count: int, proxy: Optional[ProxySettings]) -> str:
        server = proxy.get("server", "direct") if proxy else "direct"
        return (
            f"Dry-run siap untuk {count} akun. Proxy pertama {server} akan dipakai "
            "oleh signup dan client login. Tidak ada proses eksternal dijalankan."
        )

    def _write_client_error(self, email: str, exc: Exception) -> None:
        self._write_client_error_line(f"Unhandled client error for {email}: {exc}")
