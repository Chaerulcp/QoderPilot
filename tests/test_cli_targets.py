from __future__ import annotations

import asyncio
import unittest
from unittest.mock import Mock, patch

from qoderpilot import cli
from qoderpilot.pipeline import PipelineError


class CliTargetTests(unittest.TestCase):
    @staticmethod
    def _args(argv: list[str]):
        return cli.build_parser().parse_args(argv)

    def test_patch_prompts_for_target_when_flag_missing(self) -> None:
        args = self._args(["patch"])
        app = Mock()
        app.patch_client.return_value = True

        with patch("builtins.input", return_value="2"):
            exit_code = asyncio.run(cli.execute(args, app))

        self.assertEqual(exit_code, 0)
        app.patch_client.assert_called_once_with("agentic")

    def test_patch_target_flag_skips_prompt(self) -> None:
        args = self._args(["patch", "--target", "ide"])
        app = Mock()
        app.patch_client.return_value = True

        with patch("builtins.input", side_effect=AssertionError("prompt tidak diharapkan")):
            exit_code = asyncio.run(cli.execute(args, app))

        self.assertEqual(exit_code, 0)
        app.patch_client.assert_called_once_with("ide")

    def test_patch_failure_returns_error_code(self) -> None:
        args = self._args(["patch", "--target", "agentic"])
        app = Mock()
        app.patch_client.return_value = False

        exit_code = asyncio.run(cli.execute(args, app))

        self.assertEqual(exit_code, 2)

    def test_reset_with_yes_dispatches_target(self) -> None:
        args = self._args(["reset", "--target", "agentic", "--yes"])
        app = Mock()
        app.reset_client.return_value = True

        exit_code = asyncio.run(cli.execute(args, app))

        self.assertEqual(exit_code, 0)
        app.reset_client.assert_called_once_with(deep=False, target="agentic")

    def test_reset_prompts_target_then_confirmation(self) -> None:
        args = self._args(["reset", "--deep"])
        app = Mock()
        app.reset_client.return_value = True

        with patch("builtins.input", side_effect=["2", "y"]):
            exit_code = asyncio.run(cli.execute(args, app))

        self.assertEqual(exit_code, 0)
        app.reset_client.assert_called_once_with(deep=True, target="agentic")

    def test_reset_cancelled_confirmation_keeps_data(self) -> None:
        args = self._args(["reset"])
        app = Mock()

        with patch("builtins.input", side_effect=["1", "n"]):
            exit_code = asyncio.run(cli.execute(args, app))

        self.assertEqual(exit_code, 0)
        app.reset_client.assert_not_called()

    def test_select_target_requires_interactive_terminal(self) -> None:
        with patch("builtins.input", side_effect=EOFError):
            with self.assertRaises(PipelineError):
                cli.select_target(None)

    def test_run_and_resume_accept_no_reset_flag(self) -> None:
        self.assertTrue(self._args(["run", "--no-reset"]).no_reset)
        self.assertTrue(self._args(["resume", "--no-reset"]).no_reset)
        self.assertFalse(self._args(["run"]).no_reset)


if __name__ == "__main__":
    unittest.main()
