from __future__ import annotations

import asyncio
import base64
import socket
import socketserver
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import quote

from qoder_client.agentic import QoderAgenticAutomation
from qoder_client.automation import QoderClientAutomation
from qoder_client.proxy_bridge import AuthenticatedProxyBridge


class RecordingProxyHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        content = bytearray()
        while b"\r\n\r\n" not in content:
            chunk = self.request.recv(4096)
            if not chunk:
                break
            content.extend(chunk)
        self.server.headers = bytes(content)  # type: ignore[attr-defined]
        self.request.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")


class AgenticAuthTests(unittest.TestCase):
    def test_agentic_accepts_only_its_qoder_app_callback(self) -> None:
        device_url = (
            "https://www.qoder.com/device/selectAccounts?nonce=test-nonce"
            "&challenge=test-challenge&challenge_method=S256"
            "&redirect_uri=qoder-app%3A%2F%2F&machine_id=test-machine"
        )
        callback = device_url.removeprefix("https://www.qoder.com")
        sign_in_url = (
            "https://www.qoder.com/users/sign-in?oauth_callback="
            + quote(callback, safe="")
        )

        self.assertEqual(
            QoderAgenticAutomation._extract_device_auth_url(sign_in_url),
            device_url,
        )
        self.assertFalse(QoderClientAutomation._is_valid_device_auth_url(device_url))

    def test_launcher_version_supports_utf16_install_manifest(self) -> None:
        automation = object.__new__(QoderAgenticAutomation)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            automation.launcher_path = root / "Qoder Launcher.exe"
            (root / "install.ini").write_text(
                "[launcher]\ntargetVersion=0.1.2\n",
                encoding="utf-16",
            )

            version = automation.get_agentic_version()

        self.assertEqual(version, "0.1.2")

    def test_session_cleanup_preserves_machine_id_and_application_data(self) -> None:
        automation = object.__new__(QoderAgenticAutomation)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            automation.data_dir = root / "com.qoder.app.stable"
            automation.status_file = root / ".qoder" / ".qoder-app-status.json"
            automation.data_dir.mkdir()
            automation.status_file.parent.mkdir()

            auth = automation.data_dir / "auth.v1.dat"
            lock = automation.data_dir / "auth.v1.lock"
            machine = automation.data_dir / "auth.machine-id"
            database = automation.data_dir / "main.sqlite"
            for path in (auth, lock, machine, database, automation.status_file):
                path.write_text("keep-or-remove", encoding="utf-8")

            result = automation.clear_agentic_session()

            self.assertTrue(result)
            self.assertFalse(auth.exists())
            self.assertFalse(lock.exists())
            self.assertFalse(automation.status_file.exists())
            self.assertTrue(machine.exists())
            self.assertTrue(database.exists())

    def test_auth_success_must_appear_after_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "main.log"
            log.write_text("[Auth] Device login completed\n", encoding="utf-8")
            checkpoint = (log, log.stat().st_size)

            self.assertIsNone(
                QoderAgenticAutomation._agentic_auth_log_status(checkpoint)
            )
            with log.open("a", encoding="utf-8") as stream:
                stream.write("[Auth] Device login started\n")
                stream.write("[Auth] Device login completed\n")

            self.assertTrue(
                QoderAgenticAutomation._agentic_auth_log_status(checkpoint)
            )

    def test_closed_success_page_still_waits_for_agentic_log(self) -> None:
        automation = object.__new__(QoderAgenticAutomation)
        automation._submit_native_credentials = AsyncMock(
            side_effect=RuntimeError(
                "Page.wait_for_timeout: Target page, context or browser has been closed"
            )
        )

        result = asyncio.run(
            automation._submit_agentic_credentials(
                Mock(),
                "user@example.com",
                "secret",
            )
        )

        self.assertTrue(result)

    def test_agentic_waits_for_enter_before_scanning_browser(self) -> None:
        automation = object.__new__(QoderAgenticAutomation)
        events: list[str] = []

        async def capture(attempts: int = 6) -> str:
            events.append(f"capture:{attempts}")
            return "https://qoder.com/device/selectAccounts?valid=test"

        automation._capture_device_auth_url = capture
        with patch(
            "builtins.input",
            side_effect=lambda _prompt: events.append("enter"),
        ):
            result = asyncio.run(automation._obtain_agentic_auth_url())

        self.assertEqual(events, ["enter", "capture:10"])
        self.assertIn("selectAccounts", result)

    def test_launcher_inherits_the_same_authenticated_proxy(self) -> None:
        automation = object.__new__(QoderAgenticAutomation)
        automation.proxy = {
            "server": "http://proxy.example:9000",
            "username": "agentic-user",
            "password": "agentic-secret",
        }

        environment = automation._proxy_environment()

        self.assertEqual(
            environment["HTTPS_PROXY"],
            "http://agentic-user:agentic-secret@proxy.example:9000",
        )

    def test_local_bridge_adds_upstream_proxy_authorization(self) -> None:
        with socketserver.ThreadingTCPServer(
            ("127.0.0.1", 0),
            RecordingProxyHandler,
        ) as upstream:
            upstream_thread = threading.Thread(
                target=upstream.serve_forever,
                daemon=True,
            )
            upstream_thread.start()
            upstream_url = (
                f"http://bridge-user:bridge-pass@127.0.0.1:{upstream.server_address[1]}"
            )
            with AuthenticatedProxyBridge(("127.0.0.1", 0), upstream_url) as bridge:
                bridge_thread = threading.Thread(
                    target=bridge.serve_forever,
                    daemon=True,
                )
                bridge_thread.start()
                with socket.create_connection(bridge.server_address, timeout=2) as client:
                    client.sendall(
                        b"CONNECT qoder.com:443 HTTP/1.1\r\n"
                        b"Host: qoder.com:443\r\n\r\n"
                    )
                    response = client.recv(4096)
                bridge.shutdown()
            upstream.shutdown()

        token = base64.b64encode(b"bridge-user:bridge-pass")
        self.assertIn(b"200 Connection Established", response)
        self.assertIn(b"Proxy-Authorization: Basic " + token, upstream.headers)

    def test_launch_sequence_clears_session_before_starting_launcher(self) -> None:
        automation = object.__new__(QoderAgenticAutomation)
        automation.launcher_path = Path("C:/ProgramData/Qoder/Qoder Launcher/Qoder Launcher.exe")
        automation.binary_path = "C:/Program Files/Qoder/Qoder/Qoder.exe"
        automation.proxy = {
            "server": "http://proxy.example:9000",
            "username": "user",
            "password": "secret",
        }
        automation.process = None
        automation.proxy_bridge_process = None
        automation.proxy_bridge_control = None
        events: list[str] = []
        launched_commands: list[list[str]] = []
        launched_environments: list[dict[str, str]] = []
        automation.check_agentic_installed = Mock(return_value=True)
        automation.kill_agentic_process = Mock(side_effect=lambda: events.append("kill"))
        automation.clear_agentic_session = Mock(
            side_effect=lambda: events.append("clear") or True
        )
        automation._agentic_process_ids = Mock(return_value=[1234])
        automation._start_authenticated_proxy_bridge = Mock(
            return_value="http://127.0.0.1:54321"
        )
        automation._set_proxy_bridge_targets = Mock(return_value=True)

        def launch(command: list[str], **_kwargs: object) -> Mock:
            launched_commands.append(command)
            launched_environments.append(_kwargs["env"])  # type: ignore[arg-type]
            events.append("launch")
            return Mock()

        with (
            patch("qoder_client.agentic.subprocess.Popen", side_effect=launch),
            patch("qoder_client.agentic.time.sleep"),
        ):
            result = automation.launch_agentic()

        self.assertTrue(result)
        self.assertEqual(events, ["kill", "clear", "launch"])
        self.assertIn(
            "--proxy-server=http://127.0.0.1:54321",
            launched_commands[0],
        )
        self.assertEqual(
            launched_environments[0]["HTTPS_PROXY"],
            "http://127.0.0.1:54321",
        )
        self.assertNotIn("user", " ".join(launched_commands[0]))


if __name__ == "__main__":
    unittest.main()
