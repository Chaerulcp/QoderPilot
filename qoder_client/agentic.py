"""Qoder Agentic login automation for the Windows launcher application."""

from __future__ import annotations

import asyncio
import configparser
import json
import os
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from . import automation as desktop

AGENTIC_MACHINE_ID_FILE = "auth.machine-id"
AGENTIC_SESSION_FILES = ("auth.v1.dat", "auth.v1.lock")
AGENTIC_ONBOARDING_FILE = "first-launch-onboarding.v1.json"
AGENTIC_PREFERENCES_FILE = "Preferences"
AGENTIC_PATCH_INFO_FILE = "patch_info.json"
AGENTIC_INSTALLATION_ID_FILE = "installation_id"
AGENTIC_HOME_AUTH_DIR = ".auth"


class QoderAgenticAutomation(desktop.QoderClientAutomation):
    """Authenticate an account in the standalone Qoder Agentic application."""

    DEVICE_REDIRECT_SCHEMES = {"qoder-app"}
    DEFAULT_LAUNCHER = Path("C:/ProgramData/Qoder/Qoder Launcher/Qoder Launcher.exe")
    DEFAULT_BINARY = Path("C:/Program Files/Qoder/Qoder/Qoder.exe")

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 120000,
        proxy: Optional[Dict[str, str]] = None,
    ) -> None:
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy
        self.process: Optional[subprocess.Popen[Any]] = None
        self.proxy_bridge_process: Optional[subprocess.Popen[Any]] = None
        self.proxy_bridge_control: Optional[Path] = None
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.credits: Optional[int] = None
        self.platform = "Windows"
        self.launcher_path = Path(
            os.getenv("QODER_AGENTIC_LAUNCHER", str(self.DEFAULT_LAUNCHER))
        )
        self.binary_path = os.getenv("QODER_AGENTIC_BINARY", str(self.DEFAULT_BINARY))
        appdata = Path(os.getenv("APPDATA", str(Path.home() / "AppData/Roaming")))
        self.data_dir = Path(
            os.getenv(
                "QODER_AGENTIC_DATA_DIR",
                str(appdata / "com.qoder.app.stable"),
            )
        )
        self.home_dir = Path(
            os.getenv("QODER_AGENTIC_HOME_DIR", str(Path.home() / ".qoder"))
        )
        self.status_file = self.home_dir / ".qoder-app-status.json"
        desktop.write_log(
            f"Initialized QoderAgenticAutomation (headless={headless})",
            "INFO",
        )

    def check_agentic_installed(self) -> bool:
        missing = [
            path
            for path in (self.launcher_path, Path(self.binary_path))
            if not path.is_file()
        ]
        if missing:
            for path in missing:
                desktop.print_color(
                    f"  [!] File Qoder Agentic tidak ditemukan: {path}",
                    desktop.Colors.RED,
                )
            desktop.write_log(
                "Qoder Agentic installation incomplete: "
                + ", ".join(str(path) for path in missing),
                "ERROR",
            )
            return False

        desktop.print_color(
            f"  [OK] Qoder Agentic Launcher: {self.launcher_path}",
            desktop.Colors.GREEN,
        )
        return True

    def get_agentic_version(self) -> Optional[str]:
        manifest = self.launcher_path.parent / "install.ini"
        parser = configparser.ConfigParser()
        try:
            raw = manifest.read_bytes()
            encoding = (
                "utf-16"
                if raw.startswith((b"\xff\xfe", b"\xfe\xff"))
                else "utf-8-sig"
            )
            parser.read_string(raw.decode(encoding))
            version = parser.get("launcher", "targetVersion", fallback="").strip()
        except (OSError, UnicodeError, configparser.Error):
            version = ""
        if not version:
            return None
        desktop.print_color(f"  [*] Qoder Agentic Version: {version}", desktop.Colors.CYAN)
        desktop.write_log(f"Qoder Agentic version: {version}", "INFO")
        return version

    def _agentic_process_ids(self) -> list[int]:
        target = str(Path(self.binary_path).resolve()).replace("'", "''")
        script = (
            f"$target = [IO.Path]::GetFullPath('{target}'); "
            "Get-Process -Name Qoder -ErrorAction SilentlyContinue | "
            "Where-Object { $_.Path -eq $target } | "
            "ForEach-Object { $_.Id }"
        )
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return []
        return [
            int(line.strip())
            for line in result.stdout.splitlines()
            if line.strip().isdigit()
        ]

    def kill_agentic_process(self) -> None:
        for process_id in self._agentic_process_ids():
            subprocess.run(
                ["taskkill", "/F", "/PID", str(process_id)],
                capture_output=True,
                text=True,
                check=False,
            )
        subprocess.run(
            ["taskkill", "/F", "/IM", "Qoder Launcher.exe"],
            capture_output=True,
            text=True,
            check=False,
        )
        time.sleep(2)
        desktop.write_log("Stopped existing Qoder Agentic processes", "INFO")

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            path.resolve().relative_to(root.resolve())
        except (OSError, ValueError):
            return False
        return True

    def clear_agentic_session(self) -> bool:
        """Remove Agentic authentication only; retain machine ID and user data."""
        data_root = self.data_dir.resolve()
        targets = [
            data_root / "auth.v1.dat",
            data_root / "auth.v1.lock",
            self.status_file,
        ]
        removed = 0
        try:
            for target in targets:
                allowed_root = (
                    data_root if target.parent == data_root else self.status_file.parent
                )
                if not self._is_within(target, allowed_root):
                    raise OSError(
                        f"Target sesi berada di luar direktori yang diizinkan: {target}"
                    )
                if target.is_file() or target.is_symlink():
                    target.unlink()
                    removed += 1
        except OSError as exc:
            desktop.write_log(f"Could not clear Qoder Agentic session: {exc}", "ERROR")
            desktop.print_color(
                f"  [!] Gagal membersihkan sesi Agentic: {exc}",
                desktop.Colors.RED,
            )
            return False

        desktop.write_log(f"Cleared {removed} Qoder Agentic auth file(s)", "SUCCESS")
        desktop.print_color(
            "  [OK] Sesi akun lama Qoder Agentic sudah dibersihkan.",
            desktop.Colors.GREEN,
        )
        return True

    def patch_identity(self) -> bool:
        """Replace Agentic device identifiers while retaining application data."""
        desktop.print_color(
            "  [*] Patching identitas Qoder Agentic...", desktop.Colors.YELLOW
        )
        desktop.write_log("Starting Qoder Agentic identity patch", "INFO")
        try:
            self.kill_agentic_process()
            if not self.clear_agentic_session():
                return False
            machine_id = self._write_new_machine_id()
            device_salt = self._rotate_device_id_salt()
            self._remove_onboarding_identity()
            if not self.remove_agentic_home_identity():
                desktop.write_log(
                    "Qoder Agentic patch failed: home identity still present",
                    "ERROR",
                )
                return False
            self._write_agentic_patch_info(machine_id, device_salt)
        except OSError as exc:
            desktop.write_log(f"Qoder Agentic patch failed: {exc}", "ERROR")
            desktop.print_color(
                f"  [!] Patch Qoder Agentic gagal: {exc}", desktop.Colors.RED
            )
            return False

        desktop.write_log("Qoder Agentic identity patch completed", "SUCCESS")
        desktop.print_color(
            "  [OK] Patch Qoder Agentic selesai!", desktop.Colors.GREEN
        )
        desktop.print_color(f"  machine-id: {machine_id}", desktop.Colors.CYAN)
        return True

    def _write_new_machine_id(self) -> str:
        machine_id = str(uuid.uuid4())
        self.data_dir.mkdir(parents=True, exist_ok=True)
        target = self.data_dir / AGENTIC_MACHINE_ID_FILE
        target.write_text(f"{machine_id}\n", encoding="utf-8")
        desktop.write_log("Generated new Agentic machine ID", "INFO")
        return machine_id

    def _rotate_device_id_salt(self) -> str:
        salt = uuid.uuid4().hex.upper()
        preferences_path = self.data_dir / AGENTIC_PREFERENCES_FILE
        preferences = self._load_agentic_preferences(preferences_path)
        electron = preferences.get("electron")
        if not isinstance(electron, dict):
            electron = {}
            preferences["electron"] = electron
        media = electron.get("media")
        if not isinstance(media, dict):
            media = {}
            electron["media"] = media
        media["device_id_salt"] = salt
        preferences_path.write_text(
            json.dumps(preferences, separators=(",", ":")), encoding="utf-8"
        )
        desktop.write_log("Rotated Agentic device_id_salt", "INFO")
        return salt

    @staticmethod
    def _load_agentic_preferences(path: Path) -> Dict[str, Any]:
        if not path.is_file():
            return {}
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            desktop.write_log(f"Could not read Agentic preferences: {exc}", "WARNING")
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def _remove_onboarding_identity(self) -> None:
        onboarding = self.data_dir / AGENTIC_ONBOARDING_FILE
        if not onboarding.is_file():
            return
        onboarding.unlink()
        desktop.write_log("Removed Agentic onboarding identity", "INFO")

    def remove_agentic_home_identity(self) -> bool:
        """Remove persistent identifiers kept outside the application data dir.

        The agent runtime stores an installation ID and a machine ID in the
        shared ~/.qoder home. Both must be removed so a new login is seen
        as a brand-new device.
        """
        if not self.home_dir.exists():
            return True

        home_root = self.home_dir.resolve()
        success = True
        for target in (
            home_root / AGENTIC_INSTALLATION_ID_FILE,
            home_root / AGENTIC_HOME_AUTH_DIR,
        ):
            if not target.exists() and not target.is_symlink():
                continue
            try:
                target.resolve().relative_to(home_root)
            except ValueError:
                desktop.write_log(
                    f"Skip identitas Agentic di luar home: {target}",
                    "WARNING",
                )
                continue
            if target.is_dir() and not target.is_symlink():
                if not _remove_agentic_tree(target):
                    success = False
            else:
                try:
                    target.unlink()
                    desktop.print_color(
                        f"  [OK] Removed: {target}",
                        desktop.Colors.CYAN,
                    )
                    desktop.write_log(
                        f"Removed Agentic home identity: {target.name}",
                        "INFO",
                    )
                except OSError as exc:
                    desktop.write_log(
                        f"Could not remove {target}: {exc}",
                        "ERROR",
                    )
                    desktop.print_color(
                        f"  [!] Gagal menghapus: {target}",
                        desktop.Colors.RED,
                    )
                    success = False
        return success

    def _write_agentic_patch_info(self, machine_id: str, device_salt: str) -> None:
        info = {
            "target": "agentic",
            "platform": self.platform,
            "machine_id": machine_id,
            "device_id_salt": device_salt,
            "patched_at": datetime.now(timezone.utc).isoformat(),
        }
        patch_info = self.data_dir / AGENTIC_PATCH_INFO_FILE
        patch_info.write_text(json.dumps(info, indent=2), encoding="utf-8")

    def _agentic_is_running(self) -> bool:
        return bool(self._agentic_process_ids())

    @staticmethod
    def _agentic_proxy_environment(proxy_endpoint: Optional[str]) -> Dict[str, str]:
        environment = os.environ.copy()
        if not proxy_endpoint:
            return environment
        environment["HTTP_PROXY"] = proxy_endpoint
        environment["HTTPS_PROXY"] = proxy_endpoint
        environment["ALL_PROXY"] = proxy_endpoint
        environment["NO_PROXY"] = "localhost,127.0.0.1,::1"
        return environment

    def launch_agentic(self) -> bool:
        if not self.check_agentic_installed():
            return False
        self.kill_agentic_process()
        if not self.clear_agentic_session():
            return False

        proxy_endpoint = self.proxy.get("server") if self.proxy else None
        uses_authenticated_bridge = bool(
            self.proxy
            and self.proxy.get("server")
            and self.proxy.get("username")
        )
        if uses_authenticated_bridge:
            proxy_endpoint = self._start_authenticated_proxy_bridge()
            if not proxy_endpoint:
                desktop.print_color(
                    "  [!] Relay autentikasi proxy Agentic gagal dimulai.",
                    desktop.Colors.RED,
                )
                return False

        try:
            desktop.print_color(
                f"  [*] Membuka Qoder Agentic melalui: {self.launcher_path}",
                desktop.Colors.YELLOW,
            )
            environment = self._agentic_proxy_environment(proxy_endpoint)
            command = [str(self.launcher_path)]
            if proxy_endpoint:
                command.extend(
                    [
                        f"--proxy-server={proxy_endpoint}",
                        "--proxy-bypass-list=<-loopback>",
                    ]
                )
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=environment,
            )
            if self.proxy and self.proxy.get("server"):
                desktop.write_log(
                    f"Qoder Agentic process proxy: {self.proxy['server']}",
                    "INFO",
                )
            time.sleep(8)
        except OSError as exc:
            self._stop_proxy_bridge()
            desktop.write_log(f"Could not launch Qoder Agentic: {exc}", "ERROR")
            desktop.print_color(
                f"  [!] Qoder Agentic gagal dibuka: {exc}",
                desktop.Colors.RED,
            )
            return False

        process_ids = self._agentic_process_ids()
        if not process_ids:
            self._stop_proxy_bridge()
            desktop.write_log("Qoder Agentic process was not found after launch", "ERROR")
            desktop.print_color("  [!] Proses Qoder Agentic tidak terdeteksi.", desktop.Colors.RED)
            return False
        if not self._set_proxy_bridge_targets(process_ids):
            return False
        desktop.print_color("  [OK] Qoder Agentic berhasil dibuka.", desktop.Colors.GREEN)
        return True

    def _latest_agentic_log(self) -> Optional[Path]:
        try:
            logs = list((self.data_dir / "logs").rglob("main.log"))
            return max(logs, key=lambda path: path.stat().st_mtime)
        except (OSError, ValueError):
            return None

    def _agentic_log_checkpoint(self) -> tuple[Optional[Path], int]:
        latest = self._latest_agentic_log()
        if latest is None:
            return None, 0
        try:
            return latest, latest.stat().st_size
        except OSError:
            return None, 0

    @staticmethod
    def _agentic_auth_log_status(
        checkpoint: tuple[Optional[Path], int],
    ) -> Optional[bool]:
        path, offset = checkpoint
        if path is None:
            return None
        try:
            with path.open("rb") as stream:
                stream.seek(offset)
                content = stream.read().decode("utf-8", errors="replace")
        except OSError:
            return None

        success = content.rfind("[Auth] Device login completed")
        failure = max(
            content.rfind("[Auth] Device login failed"),
            content.rfind("[Auth] Device login canceled"),
            content.rfind("[Auth] Device login cancelled"),
        )
        if success < 0 and failure < 0:
            return None
        return success > failure

    async def _obtain_agentic_auth_url(self) -> Optional[str]:
        """Wait for explicit confirmation before examining any browser window."""
        desktop.print_color(
            "  [ACTION] Klik 'Sign In' pada Qoder Agentic.",
            desktop.Colors.CYAN,
        )
        print("  [*] Tunggu sampai tab login Qoder terbuka di browser.")
        try:
            input(
                f"{desktop.Colors.YELLOW}Tekan Enter setelah tab login sudah terbuka..."
                f"{desktop.Colors.RESET}"
            )
        except EOFError:
            desktop.write_log(
                "Qoder Agentic login requires an interactive Enter confirmation",
                "ERROR",
            )
            desktop.print_color(
                "  [!] Terminal tidak dapat menerima tombol Enter.",
                desktop.Colors.RED,
            )
            return None
        print("  [*] Mencari URL PKCE Qoder Agentic dari tab yang baru...")
        return await self._capture_device_auth_url(attempts=10)

    @staticmethod
    def _register_agentic_redirect_capture(
        page: Any,
        state: Dict[str, Optional[str]],
    ) -> None:
        def capture_url(url: str) -> None:
            if url.startswith("qoder-app://"):
                state["url"] = url

        page.on("request", lambda request: capture_url(request.url))
        page.on("framenavigated", lambda frame: capture_url(frame.url))

    @staticmethod
    def _open_agentic_protocol(url: str) -> bool:
        if not url.startswith("qoder-app://"):
            return False
        try:
            os.startfile(url)  # type: ignore[attr-defined]
        except OSError as exc:
            desktop.write_log(f"Could not open qoder-app callback: {exc}", "WARNING")
            return False
        desktop.write_log("Opened authenticated qoder-app callback", "INFO")
        return True

    async def _wait_for_agentic_auth(
        self,
        page: Any,
        state: Dict[str, Optional[str]],
        checkpoint: tuple[Optional[Path], int],
        timeout: int = 120,
    ) -> bool:
        callback_opened = False
        confirmation_clicked = False
        for elapsed in range(timeout):
            latest_log = self._latest_agentic_log()
            if latest_log is not None and latest_log != checkpoint[0]:
                checkpoint = (latest_log, 0)
            status = self._agentic_auth_log_status(checkpoint)
            if status is not None:
                return status

            callback = state.get("url")
            try:
                current_url = page.url
            except Exception:
                current_url = ""
            if not callback and current_url.startswith("qoder-app://"):
                callback = current_url
            if callback and not callback_opened:
                callback_opened = self._open_agentic_protocol(callback)

            if "/device/selectAccounts" in current_url and not confirmation_clicked:
                confirmation_clicked = await self._click_device_confirmation(page)
            if "accounts.google.com" in current_url:
                desktop.write_log(
                    "Agentic email auth unexpectedly reached Google",
                    "ERROR",
                )
                return False
            error = await self._native_error_text(page)
            if error and "password" in error.lower():
                desktop.write_log(f"Qoder Agentic sign-in error: {error}", "ERROR")
                return False
            if elapsed and elapsed % 15 == 0:
                print(f"  [*] Menunggu Qoder Agentic menerima token... ({elapsed}/{timeout})")
            await asyncio.sleep(1)

        desktop.write_log("Timed out waiting for Qoder Agentic device login", "ERROR")
        return False

    async def _save_agentic_login_diagnostic(self, page: Any) -> None:
        try:
            output = Path(desktop.LOG_FILE).parent / "agentic_login_failed.png"
            await page.screenshot(path=str(output), full_page=True)
            desktop.write_log(f"Agentic login diagnostic saved to {output}", "INFO")
        except Exception as exc:
            desktop.write_log(f"Could not save Agentic login diagnostic: {exc}", "WARNING")

    async def _submit_agentic_credentials(
        self,
        page: Any,
        email: str,
        password: str,
    ) -> bool:
        """Allow the success page to close while Agentic completes device polling."""
        try:
            return await self._submit_native_credentials(page, email, password)
        except Exception as exc:
            message = str(exc).lower()
            if "target page" in message and "closed" in message:
                desktop.write_log(
                    "Agentic browser closed after credential submission; "
                    "continuing with application log verification",
                    "INFO",
                )
                return True
            raise

    async def login_via_browser(
        self,
        email: str,
        password: str,
        device_auth_url: str,
        checkpoint: tuple[Optional[Path], int],
    ) -> bool:
        desktop.print_color(
            "  [*] Login Qoder Agentic dengan email/password...",
            desktop.Colors.CYAN,
        )
        if not desktop.ensure_playwright_browsers():
            desktop.write_log("Playwright browser is unavailable", "ERROR")
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
                    self._register_agentic_redirect_capture(page, state)
                    if not await self._open_native_login_page(page, device_auth_url):
                        await self._save_agentic_login_diagnostic(page)
                        return False
                    if not await self._submit_agentic_credentials(page, email, password):
                        await self._save_agentic_login_diagnostic(page)
                        return False
                    if await self._wait_for_agentic_auth(page, state, checkpoint):
                        return True
                    await self._save_agentic_login_diagnostic(page)
                    return False
                finally:
                    try:
                        await browser.close()
                    except Exception as exc:
                        desktop.write_log(
                            f"Agentic browser cleanup warning: {exc}",
                            "WARNING",
                        )
        except Exception as exc:
            desktop.write_log(f"Qoder Agentic browser login failed: {exc}", "ERROR")
            desktop.print_color(f"  [!] Login Qoder Agentic gagal: {exc}", desktop.Colors.RED)
            return False

    async def login_to_agentic(self, email: str, password: str) -> bool:
        self.email = email
        self.password = password
        if not self.launch_agentic():
            return False
        print("  [*] Menunggu Qoder Agentic siap...")
        await asyncio.sleep(3)

        checkpoint = self._agentic_log_checkpoint()
        device_auth_url = await self._obtain_agentic_auth_url()
        if not device_auth_url:
            desktop.write_log("Could not capture a new Qoder Agentic PKCE URL", "ERROR")
            desktop.print_color(
                "  [!] URL PKCE sesi Qoder Agentic tidak ditemukan.",
                desktop.Colors.RED,
            )
            return False

        desktop.print_color(
            "  [OK] URL PKCE Qoder Agentic berhasil ditangkap.",
            desktop.Colors.GREEN,
        )
        return await self.login_via_browser(
            email,
            password,
            device_auth_url,
            checkpoint,
        )

    async def run_client_login(
        self,
        email: str,
        password: str,
    ) -> Optional[Dict[str, Any]]:
        print(f"\n{desktop.Colors.CYAN}{'=' * 50}{desktop.Colors.RESET}")
        print(f"{desktop.Colors.CYAN}QODER AGENTIC LOGIN: {email}{desktop.Colors.RESET}")
        print(f"{desktop.Colors.CYAN}{'=' * 50}{desktop.Colors.RESET}")
        if self.proxy and self.proxy.get("server"):
            desktop.print_color(f"Proxy: {self.proxy['server']}", desktop.Colors.CYAN)
            await asyncio.to_thread(self.verify_outbound_ip)

        if not self.check_agentic_installed():
            return None
        self.get_agentic_version()
        if not await self.login_to_agentic(email, password):
            desktop.save_failed(email, "Qoder Agentic login failed")
            return None

        data = {
            "credits": None,
            "email": email,
            "client_login": True,
            "platform": "Windows",
            "target": "Qoder Agentic",
        }
        desktop.save_success(email, data)
        desktop.remove_account(email)
        desktop.print_color("  [OK] Qoder Agentic berhasil login.", desktop.Colors.GREEN)
        return {"success": True, "credits": None, "target": "agentic"}


# ================= AGENTIC PATCH & RESET FUNCTIONS =================

def patch_agentic() -> bool:
    """Patch Qoder Agentic identity data only."""
    return QoderAgenticAutomation().patch_identity()


def reset_agentic_completely() -> bool:
    """Reset Qoder Agentic data, then apply a fresh identity patch."""
    desktop.print_color("\n[*] Resetting Qoder Agentic completely...", desktop.Colors.YELLOW)
    desktop.write_log("Starting complete Qoder Agentic reset", "INFO")
    automation = QoderAgenticAutomation()
    automation.kill_agentic_process()
    if not _remove_agentic_state(automation):
        return False
    _recreate_agentic_dirs(automation)
    if not automation.patch_identity():
        return False
    desktop.print_color("\n[OK] Reset Qoder Agentic selesai!", desktop.Colors.GREEN)
    desktop.write_log("Qoder Agentic reset completed", "SUCCESS")
    return True


def reset_agentic_deep() -> bool:
    """Deep reset - menghapus seluruh data Qoder Agentic tanpa re-patch."""
    desktop.print_color("\n[*] Deep resetting Qoder Agentic...", desktop.Colors.YELLOW)
    desktop.write_log("Starting Qoder Agentic deep reset", "INFO")
    automation = QoderAgenticAutomation()
    automation.kill_agentic_process()
    if not _remove_agentic_state(automation):
        return False
    _recreate_agentic_dirs(automation)
    desktop.print_color("  [OK] Deep reset Qoder Agentic selesai!", desktop.Colors.GREEN)
    desktop.write_log("Qoder Agentic deep reset completed", "SUCCESS")
    return True


def _remove_agentic_state(automation: QoderAgenticAutomation) -> bool:
    success = True
    status_file = automation.status_file
    if status_file.is_file():
        try:
            status_file.unlink()
            desktop.print_color(f"  [OK] Removed: {status_file}", desktop.Colors.CYAN)
        except OSError as exc:
            desktop.write_log(f"Could not remove {status_file}: {exc}", "WARNING")
            desktop.print_color(f"  [!] Gagal menghapus: {status_file}", desktop.Colors.YELLOW)
            success = False
    if automation.data_dir.exists() and not _remove_agentic_tree(automation.data_dir):
        success = False
    if not automation.remove_agentic_home_identity():
        success = False
    return success


def _remove_agentic_tree(path: Path) -> bool:
    """Remove a directory tree, retrying once after clearing file attributes."""
    shutil.rmtree(path, ignore_errors=True)
    if not path.exists():
        desktop.print_color(f"  [OK] Removed: {path}", desktop.Colors.CYAN)
        return True
    for item in path.rglob("*"):
        try:
            if item.is_symlink() or item.is_file():
                item.chmod(0o777)
                item.unlink()
        except OSError as exc:
            desktop.write_log(f"Skip {item}: {exc}", "WARNING")
    shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        desktop.write_log(f"Could not fully remove {path}", "ERROR")
        desktop.print_color(f"  [!] Tidak dapat menghapus sepenuhnya: {path}", desktop.Colors.YELLOW)
        return False
    desktop.print_color(f"  [OK] Removed: {path}", desktop.Colors.CYAN)
    return True


def _recreate_agentic_dirs(automation: QoderAgenticAutomation) -> None:
    automation.data_dir.mkdir(parents=True, exist_ok=True)
    desktop.print_color(f"  [OK] Recreated: {automation.data_dir}", desktop.Colors.CYAN)
