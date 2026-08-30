from __future__ import annotations

import string
import unittest

from qoder_creator.utils import generate_password


class GeneratePasswordTests(unittest.TestCase):
    def test_default_length_within_qoder_policy(self) -> None:
        password = generate_password()

        self.assertEqual(len(password), 14)
        self.assertTrue(8 <= len(password) <= 20)

    def test_always_contains_upper_lower_and_digit(self) -> None:
        for _ in range(500):
            password = generate_password()

            self.assertTrue(
                any(ch.isupper() for ch in password), f"no uppercase: {password!r}"
            )
            self.assertTrue(
                any(ch.islower() for ch in password), f"no lowercase: {password!r}"
            )
            self.assertTrue(
                any(ch.isdigit() for ch in password), f"no digit: {password!r}"
            )

    def test_only_alphanumeric_characters(self) -> None:
        allowed = set(string.ascii_letters + string.digits)

        for _ in range(200):
            password = generate_password()

            self.assertTrue(set(password) <= allowed, f"bad chars in {password!r}")

    def test_length_clamped_to_8_20(self) -> None:
        self.assertEqual(len(generate_password(4)), 8)
        self.assertEqual(len(generate_password(99)), 20)
        self.assertEqual(len(generate_password(12)), 12)


if __name__ == "__main__":
    unittest.main()