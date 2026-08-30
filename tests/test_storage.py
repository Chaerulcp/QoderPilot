from __future__ import annotations

import tempfile
import unittest
import urllib.request
from pathlib import Path

from qoder_client.automation import QoderClientAutomation
from qoder_creator.proxy import proxy_url
from qoder_creator.tempmail import TempikClient
from qoderpilot.models import PendingJob
from qoderpilot.storage import PendingJobStore


class StorageTests(unittest.TestCase):
    def test_pending_job_keeps_proxy_credentials_for_resume(self) -> None:
        proxy = {
            "server": "http://127.0.0.1:8080",
            "username": "user",
            "password": "pass",
        }
        with tempfile.TemporaryDirectory() as directory:
            store = PendingJobStore(Path(directory) / "pending.jsonl")
            store.upsert(PendingJob.create("user@example.com", "secret", proxy))

            saved = store.read()

            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0].proxy, proxy)

    def test_remove_deletes_only_matching_email(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = PendingJobStore(Path(directory) / "pending.jsonl")
            store.upsert(PendingJob.create("one@example.com", "one", None))
            store.upsert(PendingJob.create("two@example.com", "two", None))

            store.remove("ONE@example.com")

            self.assertEqual([item.email for item in store.read()], ["two@example.com"])

    def test_proxy_url_encodes_authentication(self) -> None:
        value = proxy_url(
            {
                "server": "http://proxy.example:9000",
                "username": "name@example.com",
                "password": "p@ss word",
            }
        )

        self.assertEqual(
            value,
            "http://name%40example.com:p%40ss%20word@proxy.example:9000",
        )

    def test_tempmail_and_qoder_process_use_authenticated_proxy(self) -> None:
        proxy = {
            "server": "http://proxy.example:9000",
            "username": "user",
            "password": "secret",
        }
        tempmail = TempikClient(proxy=proxy)
        handlers = [
            item
            for item in tempmail._opener.handlers
            if isinstance(item, urllib.request.ProxyHandler)
        ]
        automation = QoderClientAutomation.__new__(QoderClientAutomation)
        automation.proxy = proxy

        self.assertEqual(
            handlers[0].proxies["https"],
            "http://user:secret@proxy.example:9000",
        )
        self.assertEqual(
            automation._proxy_environment()["HTTPS_PROXY"],
            "http://user:secret@proxy.example:9000",
        )


class ProxyErrorHintTests(unittest.TestCase):
    def test_hint_detects_402_payment_required(self) -> None:
        from qoder_creator.proxy import proxy_error_hint
        from urllib.error import URLError

        exc = URLError("Tunnel connection failed: 402 Payment Required")

        hint = proxy_error_hint(exc)

        self.assertIsNotNone(hint)
        self.assertIn("402 Payment Required", hint)
        self.assertIn("balance/quota", hint)
        self.assertIn("proxies.txt", hint)

    def test_hint_detects_407_proxy_authentication(self) -> None:
        from qoder_creator.proxy import proxy_error_hint
        from urllib.error import URLError

        exc = URLError("Tunnel connection failed: 407 Proxy Authentication Required")

        hint = proxy_error_hint(exc)

        self.assertIsNotNone(hint)
        self.assertIn("407", hint)
        self.assertIn("username/password", hint)

    def test_hint_none_for_unrelated_errors(self) -> None:
        from qoder_creator.proxy import proxy_error_hint
        from urllib.error import URLError

        self.assertIsNone(proxy_error_hint(URLError("Connection refused")))
        self.assertIsNone(proxy_error_hint(ValueError("boom")))

    def test_tempmail_init_session_reports_proxy_402_hint(self) -> None:
        from unittest.mock import patch
        from urllib.error import URLError

        from qoder_creator.tempmail import TempMailError

        client = TempikClient(base_url="https://tempik.example/api")
        tunnel_error = URLError("Tunnel connection failed: 402 Payment Required")

        with patch.object(client._opener, "open", side_effect=tunnel_error):
            with self.assertRaises(TempMailError) as ctx:
                client.init_session()

        message = str(ctx.exception)
        self.assertIn("Unable to start a temp mail session", message)
        self.assertIn("402 Payment Required", message)
        self.assertIn("balance/quota", message)


if __name__ == "__main__":
    unittest.main()
