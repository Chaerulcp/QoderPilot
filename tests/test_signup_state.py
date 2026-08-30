from __future__ import annotations

import asyncio
import unittest

from qoder_creator.signup import SignupManager


class FakeElement:
    def __init__(self, text: str = "", visible: bool = True) -> None:
        self.text = text
        self.visible = visible

    async def is_visible(self) -> bool:
        return self.visible

    async def inner_text(self) -> str:
        return self.text


class FakeSignupPage:
    url = "https://qoder.com/users/sign-up"

    def __init__(self, otp: bool = False, error: str = "") -> None:
        self.otp = otp
        self.error = error

    async def query_selector_all(self, selector: str) -> list[FakeElement]:
        if selector == "input.ant-otp-input" and self.otp:
            return [FakeElement() for _ in range(6)]
        if selector == ".ant-message-error" and self.error:
            return [FakeElement(self.error)]
        return []

    async def wait_for_timeout(self, milliseconds: int) -> None:
        await asyncio.sleep(milliseconds / 1000)


class SignupStateTests(unittest.TestCase):
    def test_otp_form_is_required_before_mailbox_polling(self) -> None:
        ready, error = asyncio.run(
            SignupManager._wait_for_otp_step(FakeSignupPage(otp=True), timeout=20)
        )

        self.assertTrue(ready)
        self.assertEqual(error, "")

    def test_server_email_rejection_is_reported_immediately(self) -> None:
        ready, error = asyncio.run(
            SignupManager._wait_for_otp_step(
                FakeSignupPage(error="You are sending emails too frequently."),
                timeout=100,
            )
        )

        self.assertFalse(ready)
        self.assertIn("too frequently", error)


if __name__ == "__main__":
    unittest.main()
