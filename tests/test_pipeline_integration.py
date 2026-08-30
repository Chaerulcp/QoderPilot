from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from qoderpilot.config import PipelineConfig
from qoderpilot.models import PendingJob
from qoderpilot.pipeline import QoderPilot


class FakeSignup:
    def __init__(self) -> None:
        self.proxies: list[dict[str, str] | None] = []

    async def create_account(self, index: int, proxy: dict[str, str] | None) -> dict[str, str]:
        self.proxies.append(proxy)
        return {"email": f"user-{index}@example.com", "password": "secret"}


class FakeClient:
    def __init__(self, proxy: dict[str, str] | None) -> None:
        self.proxy = proxy

    async def run_client_login(self, email: str, password: str) -> dict[str, Any]:
        return {"success": True, "credits": None}


class RecordingClient:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    async def run_client_login(self, email: str, password: str) -> dict[str, Any]:
        self.events.append("login")
        return {"success": True, "credits": None}


class PipelineIntegrationTests(unittest.TestCase):
    def test_signup_and_client_receive_the_same_proxy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proxy = {
                "server": "http://127.0.0.1:8080",
                "username": "user",
                "password": "pass",
            }
            signup = FakeSignup()
            client_proxies: list[dict[str, str] | None] = []
            pipeline = QoderPilot(self._config(root))
            pipeline._require_ready = lambda: None
            pipeline._prepare_runtime = lambda: None
            pipeline._next_proxy = lambda: proxy
            pipeline._create_signup_manager = lambda: signup
            pipeline._login_target = "ide"
            pipeline._reset_target = lambda target, deep=False: True
            pipeline._create_client_automation = (
                lambda value, target: self._client(value, client_proxies)
            )

            result = asyncio.run(pipeline.run(1))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(signup.proxies, [proxy])
            self.assertEqual(client_proxies, [proxy])
            self.assertEqual(pipeline.status().pending, 0)

    def test_user_can_select_agentic_before_login_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = QoderPilot(self._config(Path(directory)))

            with patch("builtins.input", side_effect=["", "9", "2"]) as user_input:
                target = pipeline._select_login_target()

            self.assertEqual(target, "agentic")
            self.assertEqual(user_input.call_count, 3)

    def test_login_job_resets_target_before_client_login(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = QoderPilot(self._config(Path(directory)))
            events: list[str] = []
            pipeline._reset_target = lambda target, deep=False: events.append(f"reset:{target}") or True
            pipeline._login_target = "agentic"
            pipeline._create_client_automation = lambda proxy, target: RecordingClient(events)
            job = PendingJob.create("user@example.com", "secret", None)
            pipeline.pending.upsert(job)

            result = asyncio.run(pipeline._login_job(job))

            self.assertTrue(result)
            self.assertEqual(events, ["reset:agentic", "login"])
            self.assertEqual(pipeline.pending.read(), [])

    def test_failed_reset_keeps_job_pending_and_skips_login(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = QoderPilot(self._config(Path(directory)))
            events: list[str] = []
            pipeline._reset_target = lambda target, deep=False: False
            pipeline._login_target = "ide"
            pipeline._create_client_automation = lambda proxy, target: RecordingClient(events)
            job = PendingJob.create("user@example.com", "secret", None)
            pipeline.pending.upsert(job)

            result = asyncio.run(pipeline._login_job(job))

            self.assertFalse(result)
            self.assertEqual(events, [])
            self.assertEqual(len(pipeline.pending.read()), 1)

    def test_run_resets_every_job_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            resets: list[str] = []
            pipeline = self._ready_pipeline(Path(directory), resets)

            result = asyncio.run(pipeline.run(2))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(resets, ["ide", "ide"])

    def test_no_reset_flag_skips_the_pre_login_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            resets: list[str] = []
            pipeline = self._ready_pipeline(Path(directory), resets)

            result = asyncio.run(pipeline.run(1, no_reset=True))

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(resets, [])

    def _ready_pipeline(self, root: Path, resets: list[str]) -> QoderPilot:
        pipeline = QoderPilot(self._config(root))
        pipeline._require_ready = lambda: None
        pipeline._prepare_runtime = lambda: None
        pipeline._next_proxy = lambda: None
        pipeline._create_signup_manager = lambda: FakeSignup()
        pipeline._login_target = "ide"
        pipeline._reset_target = lambda target, deep=False: resets.append(target) or True
        pipeline._create_client_automation = lambda proxy, target: FakeClient(proxy)
        return pipeline

    @staticmethod
    def _client(
        proxy: dict[str, str] | None,
        received: list[dict[str, str] | None],
    ) -> FakeClient:
        received.append(proxy)
        return FakeClient(proxy)

    @staticmethod
    def _config(root: Path) -> PipelineConfig:
        return PipelineConfig(
            config_path=root / "config.toml",
            project_root=root,
            data_dir=root / "data",
            tempmail_base="https://mail.example.test/api",
            proxy_mode="file",
            proxy_file=root / "proxies.txt",
            signup_headless=True,
            client_headless=False,
            platform="Windows",
            default_count=1,
            delay_min_seconds=0,
            delay_max_seconds=0,
        )


if __name__ == "__main__":
    unittest.main()
