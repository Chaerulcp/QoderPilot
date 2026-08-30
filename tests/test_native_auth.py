from __future__ import annotations

import asyncio
import inspect
import json
import sqlite3
import tempfile
import unittest
import uuid
from contextlib import closing
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import quote

from qoder_client.automation import QoderClientAutomation, QoderPatcher


class FakeLocator:
    def __init__(self, page: "FakePage", selector: str) -> None:
        self.page = page
        self.selector = selector

    @property
    def first(self) -> "FakeLocator":
        return self

    async def is_visible(self) -> bool:
        return self.page.is_visible(self.selector)

    async def fill(self, value: str) -> None:
        self.page.filled[self.selector] = value

    async def click(self) -> None:
        self.page.clicked.append(self.selector)
        if "Continue" in self.selector:
            self.page.stage = "password"
        elif "Sign in" in self.selector:
            self.page.stage = "submitted"


class FakePage:
    def __init__(self) -> None:
        self.url = "https://qoder.com/users/sign-in"
        self.stage = "email"
        self.filled: dict[str, str] = {}
        self.clicked: list[str] = []

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self, selector)

    def is_visible(self, selector: str) -> bool:
        visible = {
            "email": {"#basic_email:visible", "button:has-text('Continue'):visible"},
            "password": {
                "#password_password:visible",
                "button:has-text('Sign in'):visible",
            },
        }
        return selector in visible.get(self.stage, set())

    async def wait_for_timeout(self, _milliseconds: int) -> None:
        return None


class NativeAuthAutomation(QoderClientAutomation):
    async def _solve_native_login_captcha(self, page: FakePage) -> bool:
        return True


class NativeAuthTests(unittest.TestCase):
    def test_native_form_uses_qoder_email_then_password(self) -> None:
        page = FakePage()
        automation = object.__new__(NativeAuthAutomation)

        success = asyncio.run(
            automation._submit_native_credentials(page, "user@example.com", "secret")
        )

        self.assertTrue(success)
        self.assertEqual(page.filled["#basic_email:visible"], "user@example.com")
        self.assertEqual(page.filled["#password_password:visible"], "secret")
        self.assertEqual(
            page.clicked,
            ["button:has-text('Continue'):visible", "button:has-text('Sign in'):visible"],
        )

    def test_browser_login_has_no_google_button_fallback(self) -> None:
        source = inspect.getsource(QoderClientAutomation.login_via_browser)

        self.assertNotIn("Sign in with Google", source)
        self.assertNotIn("accounts.google.com/o/oauth", source)

    def test_client_browser_receives_job_proxy(self) -> None:
        proxy = {
            "server": "http://127.0.0.1:8080",
            "username": "proxy-user",
            "password": "proxy-pass",
        }
        automation = object.__new__(QoderClientAutomation)
        automation.headless = True
        automation.proxy = proxy

        options = automation._client_browser_options()

        self.assertIs(options["proxy"], proxy)

    def test_pkce_url_is_extracted_from_qoder_sign_in_redirect(self) -> None:
        device_url = (
            "https://www.qoder.com/device/selectAccounts?nonce=test-nonce"
            "&challenge=test-challenge&challenge_method=S256"
            "&redirect_uri=qoder%3A%2F%2Faicoding.aicoding-agent%2Flogin-success"
            "&machine_id=test-machine"
        )
        callback = device_url.removeprefix("https://www.qoder.com")
        sign_in_url = (
            "https://www.qoder.com/users/sign-in?oauth_callback=" + quote(callback, safe="")
        )

        extracted = QoderClientAutomation._extract_device_auth_url(sign_in_url)

        self.assertEqual(extracted, device_url)

    def test_machine_id_only_url_is_rejected(self) -> None:
        invalid_url = "https://qoder.com/device/selectAccounts?machine_id=test-machine"

        self.assertFalse(QoderClientAutomation._is_valid_device_auth_url(invalid_url))
        self.assertIsNone(QoderClientAutomation._extract_device_auth_url(invalid_url))

    def test_windows_version_check_does_not_start_qoder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "resources" / "app" / "package.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"version": "1.24.2"}), encoding="utf-8")
            automation = object.__new__(QoderClientAutomation)
            automation.platform = "Windows"
            automation.binary_path = str(root / "Qoder.exe")

            with patch("qoder_client.automation.subprocess.run") as run:
                version = automation.get_qoder_version()

            self.assertEqual(version, "1.24.2")
            run.assert_not_called()

    def test_login_flow_does_not_patch_or_accept_manual_success(self) -> None:
        source = inspect.getsource(QoderClientAutomation.login_to_qoder_client)

        self.assertNotIn("patch_qoder_data", source)
        self.assertNotIn("input(", source)
        self.assertIn("_wait_for_desktop_auth", source)

    def test_desktop_auth_requires_current_log_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "renderer.log"
            log.write_text("old Login completed for user: stale\n", encoding="utf-8")
            checkpoint = (log, log.stat().st_size)

            self.assertIsNone(QoderClientAutomation._auth_log_status(checkpoint))
            with log.open("a", encoding="utf-8") as stream:
                stream.write("[QoderPkceLoginService] Login completed for user: current\n")

            self.assertTrue(QoderClientAutomation._auth_log_status(checkpoint))

    def test_missing_credit_snapshot_is_not_reported_as_300(self) -> None:
        automation = object.__new__(QoderClientAutomation)
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory)
            with (
                patch("qoder_client.automation.QODER_USER_DIR", empty / "user"),
                patch("qoder_client.automation.QODER_DATA_DIR", empty / "data"),
            ):
                credits = asyncio.run(automation.check_credits_after_login())

        self.assertIsNone(credits)
        source = inspect.getsource(QoderClientAutomation.check_credits_after_login)
        self.assertNotIn("return 300", source)

    def test_account_session_is_cleared_without_removing_settings(self) -> None:
        automation = object.__new__(QoderClientAutomation)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "Qoder"
            user = root / ".qoder"
            global_storage = data / "User" / "globalStorage"
            cache = data / "SharedClientCache" / "cache"
            global_storage.mkdir(parents=True)
            cache.mkdir(parents=True)
            user.mkdir(parents=True)

            for name in ("state.vscdb", "state.vscdb.backup"):
                database = global_storage / name
                with closing(sqlite3.connect(database)) as connection:
                    with connection:
                        connection.execute("CREATE TABLE ItemTable (key TEXT UNIQUE, value BLOB)")
                        connection.execute(
                            "INSERT INTO ItemTable VALUES (?, ?)",
                            ("secret://aicoding.auth.userInfo", "account-secret"),
                        )
                        connection.execute(
                            "INSERT INTO ItemTable VALUES (?, ?)",
                            ("workbench.sideBar.size", "320"),
                        )

            (cache / "machine_token.json").write_text("{}", encoding="utf-8")
            (cache / "status.json").write_text('{"logged_in": true}', encoding="utf-8")
            (user / ".qoder-app-status.json").write_text(
                '{"logged_in": true}', encoding="utf-8"
            )
            settings = user / "settings.json"
            settings.write_text('{"theme": "dark"}', encoding="utf-8")

            with (
                patch("qoder_client.automation.QODER_DATA_DIR", data),
                patch("qoder_client.automation.QODER_USER_DIR", user),
            ):
                result = automation.clear_qoder_account_session()

            self.assertTrue(result)
            self.assertFalse((cache / "machine_token.json").exists())
            self.assertFalse((cache / "status.json").exists())
            self.assertFalse((user / ".qoder-app-status.json").exists())
            self.assertTrue(settings.exists())
            with closing(sqlite3.connect(global_storage / "state.vscdb")) as connection:
                keys = {
                    row[0]
                    for row in connection.execute("SELECT key FROM ItemTable ORDER BY key")
                }
            self.assertNotIn("secret://aicoding.auth.userInfo", keys)
            self.assertIn("workbench.sideBar.size", keys)

    def test_launch_clears_account_session_before_starting_qoder(self) -> None:
        source = inspect.getsource(QoderClientAutomation.launch_qoder)

        self.assertLess(
            source.index("clear_qoder_account_session"),
            source.index("patch_qoder_data"),
        )

    def test_windows_manual_login_waits_for_enter_before_url_capture(self) -> None:
        automation = object.__new__(QoderClientAutomation)
        automation.platform = "Windows"
        automation._close_stale_auth_tabs = Mock(return_value=0)
        automation.click_signin_button = AsyncMock(return_value=True)
        events: list[str] = []

        async def capture(attempts: int = 6) -> str:
            events.append(f"capture:{attempts}")
            return "https://qoder.com/device/selectAccounts?valid=test"

        automation._capture_device_auth_url = capture
        with patch(
            "builtins.input", side_effect=lambda _prompt: events.append("enter")
        ):
            result = asyncio.run(automation._obtain_device_auth_url())

        self.assertEqual(events, ["enter", "capture:10"])
        self.assertIn("selectAccounts", result)
        automation._close_stale_auth_tabs.assert_not_called()
        automation.click_signin_button.assert_not_awaited()


class IdeResetAndLaunchTests(unittest.TestCase):
    def test_generated_machine_id_is_uuid4_format(self) -> None:
        patcher = QoderPatcher("Windows")

        machine_id = patcher.generate_machine_id()

        parsed = uuid.UUID(machine_id)
        self.assertEqual(parsed.version, 4)
        self.assertEqual(machine_id, patcher.machine_id)

    def test_launch_qoder_routes_authenticated_proxy_through_bridge(self) -> None:
        automation = object.__new__(QoderClientAutomation)
        automation.platform = "Windows"
        automation.proxy = {
            "server": "http://proxy.example:9000",
            "username": "user",
            "password": "secret",
        }
        automation.process = None
        automation.proxy_bridge_process = None
        automation.proxy_bridge_control = None
        automation.patcher = Mock(machine_id=None)
        automation.check_qoder_installed = Mock(return_value=True)
        automation.kill_qoder_process = Mock()
        automation.clear_qoder_account_session = Mock(return_value=True)
        automation._start_authenticated_proxy_bridge = Mock(
            return_value="http://127.0.0.1:54321"
        )
        automation._set_proxy_bridge_targets = Mock(return_value=True)
        automation._verify_machine_id_persisted = Mock()
        launched_commands: list[list[str]] = []
        launched_environments: list[dict[str, str]] = []

        def launch(command: list[str], **kwargs: object) -> Mock:
            launched_commands.append(command)
            launched_environments.append(kwargs["env"])  # type: ignore[arg-type]
            return Mock(poll=Mock(return_value=None), pid=4321)

        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "Qoder.exe"
            binary.write_text("fake", encoding="utf-8")
            automation.binary_path = str(binary)

            with (
                patch("qoder_client.automation.subprocess.Popen", side_effect=launch),
                patch("qoder_client.automation.time.sleep"),
            ):
                result = automation.launch_qoder()

        self.assertTrue(result)
        self.assertIn("--proxy-server=http://127.0.0.1:54321", launched_commands[0])
        self.assertEqual(
            launched_environments[0]["HTTPS_PROXY"],
            "http://127.0.0.1:54321",
        )
        self.assertNotIn("user", " ".join(launched_commands[0]))
        automation._set_proxy_bridge_targets.assert_called_once_with([4321])

    def test_launch_qoder_without_credentials_uses_direct_proxy(self) -> None:
        automation = object.__new__(QoderClientAutomation)
        automation.platform = "Windows"
        automation.proxy = {"server": "http://proxy.example:9000"}
        automation.process = None
        automation.proxy_bridge_process = None
        automation.proxy_bridge_control = None
        automation.patcher = Mock(machine_id=None)
        automation.check_qoder_installed = Mock(return_value=True)
        automation.kill_qoder_process = Mock()
        automation.clear_qoder_account_session = Mock(return_value=True)
        automation._start_authenticated_proxy_bridge = Mock()
        automation._verify_machine_id_persisted = Mock()
        launched_commands: list[list[str]] = []

        def launch(command: list[str], **kwargs: object) -> Mock:
            launched_commands.append(command)
            return Mock(poll=Mock(return_value=None), pid=1)

        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "Qoder.exe"
            binary.write_text("fake", encoding="utf-8")
            automation.binary_path = str(binary)

            with (
                patch("qoder_client.automation.subprocess.Popen", side_effect=launch),
                patch("qoder_client.automation.time.sleep"),
            ):
                result = automation.launch_qoder()

        self.assertTrue(result)
        self.assertIn("--proxy-server=http://proxy.example:9000", launched_commands[0])
        automation._start_authenticated_proxy_bridge.assert_not_called()

    def test_reset_qoder_completely_removes_cache_dir(self) -> None:
        from qoder_client import automation as automation_module

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "Qoder"
            user = root / ".qoder"
            cache = root / "Cache"
            for path in (data, user, cache):
                path.mkdir()
            (data / "state.vscdb").write_text("x", encoding="utf-8")
            (user / "settings.json").write_text("{}", encoding="utf-8")
            (cache / "blob.bin").write_text("cached", encoding="utf-8")

            with (
                patch.object(automation_module, "QODER_DATA_DIR", data),
                patch.object(automation_module, "QODER_USER_DIR", user),
                patch.object(automation_module, "QODER_CACHE_DIR", cache),
                patch.object(automation_module, "SELECTED_PLATFORM", "Windows"),
                patch.object(automation_module.subprocess, "run"),
                patch.object(automation_module.time, "sleep"),
            ):
                automation_module.reset_qoder_completely()

            self.assertFalse(cache.exists())
            self.assertTrue(data.exists())
            self.assertTrue(user.exists())
            machine_id = (data / "machineid").read_text(encoding="utf-8").strip()
            self.assertEqual(uuid.UUID(machine_id).version, 4)

    def test_force_remove_tree_survives_first_rmtree_failure(self) -> None:
        from qoder_client import automation as automation_module

        original_rmtree = automation_module.shutil.rmtree
        calls = {"count": 0}

        def flaky_rmtree(path, *args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise PermissionError(13, "locked", str(path))
            return original_rmtree(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            nested = root / "a" / "b" / "c"
            nested.mkdir(parents=True)
            (nested / "deep.txt").write_text("x", encoding="utf-8")
            (root / "a" / "top.txt").write_text("y", encoding="utf-8")

            with (
                patch.object(automation_module.shutil, "rmtree", side_effect=flaky_rmtree),
                patch.object(automation_module.time, "sleep"),
            ):
                removed = automation_module.force_remove_tree(root)

        self.assertTrue(removed)
        self.assertFalse(root.exists())

    def test_force_remove_tree_fallback_walk_removes_children_first(self) -> None:
        from qoder_client import automation as automation_module

        def always_locked(path, *args, **kwargs):
            raise PermissionError(13, "locked", str(path))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            nested = root / "plugins" / "cache" / "bundler" / "state"
            nested.mkdir(parents=True)
            (nested / "013b6858").write_text("state", encoding="utf-8")
            (root / "telemetry").mkdir()
            (root / "telemetry" / "events.json").write_text("{}", encoding="utf-8")

            with (
                patch.object(automation_module.shutil, "rmtree", side_effect=always_locked),
                patch.object(automation_module.time, "sleep"),
            ):
                removed = automation_module.force_remove_tree(root)

        # Regression: the old top-down walk rmdir'ed parents before their
        # children and left the tree behind with WinError 145.
        self.assertTrue(removed)
        self.assertFalse(root.exists())

    def test_reset_qoder_completely_reports_removal_failure(self) -> None:
        from qoder_client import automation as automation_module

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "Qoder"
            user = root / ".qoder"
            data.mkdir()
            user.mkdir()

            with (
                patch.object(automation_module, "QODER_DATA_DIR", data),
                patch.object(automation_module, "QODER_USER_DIR", user),
                patch.object(automation_module, "QODER_CACHE_DIR", None),
                patch.object(automation_module, "SELECTED_PLATFORM", "Windows"),
                patch.object(automation_module.subprocess, "run"),
                patch.object(automation_module.time, "sleep"),
                patch.object(automation_module, "force_remove_tree", return_value=False),
            ):
                success = automation_module.reset_qoder_completely()

        self.assertFalse(success)

    def test_verify_outbound_ip_reports_address_from_proxy(self) -> None:
        automation = object.__new__(QoderClientAutomation)
        automation.proxy = {
            "server": "http://proxy.example:9000",
            "username": "user",
            "password": "secret",
        }
        fake_response = Mock()
        fake_response.read = Mock(return_value=b"203.0.113.7\n")
        fake_response.__enter__ = Mock(return_value=fake_response)
        fake_response.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open = Mock(return_value=fake_response)

        with patch("urllib.request.build_opener", return_value=opener):
            observed = automation.verify_outbound_ip()

        self.assertEqual(observed, "203.0.113.7")

    def test_verify_outbound_ip_failure_is_not_fatal(self) -> None:
        automation = object.__new__(QoderClientAutomation)
        automation.proxy = {"server": "http://proxy.example:9000"}
        opener = Mock()
        opener.open = Mock(side_effect=OSError("proxy unreachable"))

        with patch("urllib.request.build_opener", return_value=opener):
            observed = automation.verify_outbound_ip()

        self.assertIsNone(observed)

    def test_verify_outbound_ip_can_be_skipped(self) -> None:
        automation = object.__new__(QoderClientAutomation)
        automation.proxy = {"server": "http://proxy.example:9000"}

        with (
            patch.dict("os.environ", {"QODERPILOT_SKIP_IP_CHECK": "1"}),
            patch("urllib.request.build_opener") as build_opener,
        ):
            observed = automation.verify_outbound_ip()

        self.assertIsNone(observed)
        build_opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
