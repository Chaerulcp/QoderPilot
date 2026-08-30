from __future__ import annotations

import asyncio
import io
import unittest
from typing import Any, List
from unittest.mock import patch

from rich.console import Console

from qoder_creator import signup as signup_module
from qoder_creator.captcha import solve_slider_local
from qoder_creator.signup import SignupManager, _OtpTimeout
from qoder_creator.tempmail import TempikClient


class FakeOtpPage:
    """Signup page stub whose only visible elements are the OTP inputs."""

    url = "https://qoder.com/users/sign-up"

    def __init__(self, has_otp: bool = True) -> None:
        self.has_otp = has_otp

    async def query_selector_all(self, selector: str) -> list:
        if selector == "input.ant-otp-input" and self.has_otp:
            return [FakeOtpInput() for _ in range(6)]
        return []

    async def wait_for_timeout(self, milliseconds: int) -> None:
        await asyncio.sleep(0)


class FakeOtpInput:
    async def is_visible(self) -> bool:
        return True


class SignupRestartTests(unittest.TestCase):
    @staticmethod
    def _manager() -> SignupManager:
        return SignupManager(headless=True, console=Console(file=io.StringIO()))

    def test_otp_timeout_restarts_signup_from_scratch(self) -> None:
        manager = self._manager()
        attempts: List[int] = []
        result = {"email": "user@example.com", "pat_valid": True}

        async def fake_once(idx: int, attempt: int, proxy: Any) -> Any:
            attempts.append(attempt)
            if attempt == 1:
                raise _OtpTimeout("user@example.com")
            return result

        manager._create_account_once = fake_once
        with (
            patch.object(signup_module, "SIGNUP_RETRY", 2),
            patch.object(signup_module, "OTP_RETRY_DELAY_SECONDS", 0),
        ):
            outcome = asyncio.run(manager.create_account(1))

        self.assertEqual(outcome, result)
        self.assertEqual(attempts, [1, 2])

    def test_otp_timeout_gives_up_after_max_attempts(self) -> None:
        manager = self._manager()
        attempts: List[int] = []

        async def fake_once(idx: int, attempt: int, proxy: Any) -> Any:
            attempts.append(attempt)
            raise _OtpTimeout("user@example.com")

        manager._create_account_once = fake_once
        with (
            patch.object(signup_module, "SIGNUP_RETRY", 1),
            patch.object(signup_module, "OTP_RETRY_DELAY_SECONDS", 0),
        ):
            outcome = asyncio.run(manager.create_account(1))

        self.assertIsNone(outcome)
        self.assertEqual(attempts, [1, 2])

    def test_other_failures_are_not_retried(self) -> None:
        manager = self._manager()
        attempts: List[int] = []

        async def fake_once(idx: int, attempt: int, proxy: Any) -> Any:
            attempts.append(attempt)
            return None

        manager._create_account_once = fake_once
        with patch.object(signup_module, "SIGNUP_RETRY", 2):
            outcome = asyncio.run(manager.create_account(1))

        self.assertIsNone(outcome)
        self.assertEqual(attempts, [1])


class OtpExtractionOrderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TempikClient()

    def test_newest_code_wins_over_stale_code(self) -> None:
        stale = {
            "subject": "Verify your Email with Qoder",
            "body": "Please verify your email address to start using Qoder. 111111",
            "received_at": "2026-08-30T10:00:00Z",
        }
        fresh = {
            "subject": "Verify your Email with Qoder",
            "body": "Please verify your email address to start using Qoder. 222222",
            "received_at": "2026-08-30T10:05:00Z",
        }

        self.assertEqual(self.client.extract_otp([stale, fresh]), "222222")
        self.assertEqual(self.client.extract_otp([fresh, stale]), "222222")

    def test_list_order_is_kept_without_timestamps(self) -> None:
        first = {
            "subject": "Verify your Email with Qoder",
            "body": "Please verify your email address to start using Qoder. 111111",
        }
        second = {
            "subject": "Verify your Email with Qoder",
            "body": "Please verify your email address to start using Qoder. 222222",
        }

        self.assertEqual(self.client.extract_otp([first, second]), "111111")


class GuardedPage:
    """Any page interaction fails the test loudly."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"page.{name} should not be called")


class BrokenPage:
    """Page whose captcha elements are gone (signup already advanced)."""

    def __init__(self) -> None:
        self.waits = 0

    async def click(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("captcha is gone")

    async def wait_for_function(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("captcha is gone")

    async def wait_for_timeout(self, milliseconds: int) -> None:
        self.waits += 1
        await asyncio.sleep(0)


class CaptchaSolverStopCheckTests(unittest.TestCase):
    def test_solver_returns_early_when_signup_already_advanced(self) -> None:
        async def otp_visible() -> bool:
            return True

        result = asyncio.run(
            solve_slider_local(GuardedPage(), max_attempts=3, stop_check=otp_visible)
        )

        self.assertTrue(result)

    def test_solver_continues_when_stop_check_errors(self) -> None:
        page = BrokenPage()

        async def broken_check() -> bool:
            raise RuntimeError("page closed")

        result = asyncio.run(
            solve_slider_local(page, max_attempts=2, stop_check=broken_check)
        )

        self.assertFalse(result)
        self.assertEqual(page.waits, 2)


class OtpFormVisibilityTests(unittest.TestCase):
    def test_visible_inputs_are_detected(self) -> None:
        self.assertTrue(asyncio.run(SignupManager._otp_form_visible(FakeOtpPage())))

    def test_missing_inputs_are_not_detected(self) -> None:
        self.assertFalse(
            asyncio.run(SignupManager._otp_form_visible(FakeOtpPage(has_otp=False)))
        )


if __name__ == "__main__":
    unittest.main()
