from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

from qoder_client import agentic as agentic_module
from qoder_client.agentic import (
    AGENTIC_MACHINE_ID_FILE,
    AGENTIC_ONBOARDING_FILE,
    AGENTIC_PATCH_INFO_FILE,
    QoderAgenticAutomation,
)

OLD_MACHINE_ID = "11111111-2222-4333-8444-555555555555"
OLD_SALT = "OLD00000000000000000000000000FF"


def make_automation(root: Path) -> QoderAgenticAutomation:
    automation = object.__new__(QoderAgenticAutomation)
    automation.data_dir = root / "com.qoder.app.stable"
    automation.home_dir = root / ".qoder"
    automation.status_file = automation.home_dir / ".qoder-app-status.json"
    automation.platform = "Windows"
    automation.data_dir.mkdir()
    automation.status_file.parent.mkdir()
    automation.kill_agentic_process = Mock()
    return automation


def seed_agentic_data(automation: QoderAgenticAutomation) -> None:
    data = automation.data_dir
    (data / AGENTIC_MACHINE_ID_FILE).write_text(f"{OLD_MACHINE_ID}\n", encoding="utf-8")
    (data / "auth.v1.dat").write_text("session", encoding="utf-8")
    (data / "auth.v1.lock").write_text("lock", encoding="utf-8")
    (data / AGENTIC_ONBOARDING_FILE).write_text("{}", encoding="utf-8")
    (data / "main.sqlite").write_text("db", encoding="utf-8")
    (data / "qoder-data.v1.json").write_text("{}", encoding="utf-8")
    preferences = {
        "electron": {"media": {"device_id_salt": OLD_SALT}},
        "spellcheck": {"dictionaries": ["en-US"], "dictionary": ""},
    }
    (data / "Preferences").write_text(json.dumps(preferences), encoding="utf-8")
    automation.status_file.write_text("status", encoding="utf-8")
    home = automation.home_dir
    (home / "installation_id").write_text("old-installation-id", encoding="utf-8")
    home_auth = home / ".auth"
    home_auth.mkdir(exist_ok=True)
    (home_auth / "machine_id").write_text("old-home-machine-id", encoding="utf-8")
    (home_auth / ".credential-transaction").write_text("creds", encoding="utf-8")


class AgenticIdentityPatchTests(unittest.TestCase):
    def test_patch_generates_new_identity_and_clears_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            automation = make_automation(Path(directory))
            seed_agentic_data(automation)

            result = automation.patch_identity()

            data = automation.data_dir
            self.assertTrue(result)
            automation.kill_agentic_process.assert_called_once()
            machine_id = (data / AGENTIC_MACHINE_ID_FILE).read_text(encoding="utf-8").strip()
            self.assertNotEqual(machine_id, OLD_MACHINE_ID)
            uuid.UUID(machine_id)
            self.assertFalse((data / "auth.v1.dat").exists())
            self.assertFalse((data / "auth.v1.lock").exists())
            self.assertFalse(automation.status_file.exists())
            self.assertFalse((data / AGENTIC_ONBOARDING_FILE).exists())
            home = automation.home_dir
            self.assertFalse((home / "installation_id").exists())
            self.assertFalse((home / ".auth").exists())

    def test_patch_preserves_application_data_and_preference_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            automation = make_automation(Path(directory))
            seed_agentic_data(automation)

            self.assertTrue(automation.patch_identity())

            data = automation.data_dir
            self.assertTrue((data / "main.sqlite").exists())
            self.assertTrue((data / "qoder-data.v1.json").exists())
            preferences = json.loads((data / "Preferences").read_text(encoding="utf-8"))
            new_salt = preferences["electron"]["media"]["device_id_salt"]
            self.assertNotEqual(new_salt, OLD_SALT)
            self.assertEqual(len(new_salt), 32)
            self.assertEqual(preferences["spellcheck"]["dictionaries"], ["en-US"])
            info = json.loads((data / AGENTIC_PATCH_INFO_FILE).read_text(encoding="utf-8"))
            self.assertEqual(info["target"], "agentic")
            self.assertEqual(
                info["machine_id"],
                (data / AGENTIC_MACHINE_ID_FILE).read_text(encoding="utf-8").strip(),
            )

    def test_patch_succeeds_on_a_fresh_data_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            automation = make_automation(Path(directory))
            automation.data_dir.rmdir()

            result = automation.patch_identity()

            self.assertTrue(result)
            machine = automation.data_dir / AGENTIC_MACHINE_ID_FILE
            self.assertTrue(machine.exists())
            uuid.UUID(machine.read_text(encoding="utf-8").strip())
            preferences = json.loads(
                (automation.data_dir / "Preferences").read_text(encoding="utf-8")
            )
            self.assertEqual(len(preferences["electron"]["media"]["device_id_salt"]), 32)


class AgenticResetTests(unittest.TestCase):
    def test_reset_completely_kills_then_wipes_and_repatches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            automation = make_automation(Path(directory))
            seed_agentic_data(automation)
            events: list[tuple[str, bool]] = []
            automation.kill_agentic_process = Mock(
                side_effect=lambda: events.append(
                    ("kill", (automation.data_dir / AGENTIC_MACHINE_ID_FILE).exists())
                )
            )

            with patch.object(
                agentic_module, "QoderAgenticAutomation", return_value=automation
            ):
                result = agentic_module.reset_agentic_completely()

            data = automation.data_dir
            self.assertTrue(result)
            self.assertTrue(events)
            self.assertEqual(events[0], ("kill", True))
            self.assertFalse((data / "main.sqlite").exists())
            machine = data / AGENTIC_MACHINE_ID_FILE
            self.assertTrue(machine.exists())
            self.assertNotEqual(machine.read_text(encoding="utf-8").strip(), OLD_MACHINE_ID)
            self.assertTrue((data / AGENTIC_PATCH_INFO_FILE).exists())
            home = automation.home_dir
            self.assertFalse((home / "installation_id").exists())
            self.assertFalse((home / ".auth").exists())

    def test_deep_reset_wipes_everything_without_repatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            automation = make_automation(Path(directory))
            seed_agentic_data(automation)

            with patch.object(
                agentic_module, "QoderAgenticAutomation", return_value=automation
            ):
                result = agentic_module.reset_agentic_deep()

            data = automation.data_dir
            self.assertTrue(result)
            self.assertTrue(data.exists())
            self.assertFalse((data / AGENTIC_MACHINE_ID_FILE).exists())
            self.assertFalse((data / AGENTIC_PATCH_INFO_FILE).exists())
            self.assertFalse(automation.status_file.exists())
            home = automation.home_dir
            self.assertFalse((home / "installation_id").exists())
            self.assertFalse((home / ".auth").exists())

    def test_reset_completely_fails_when_patch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            automation = make_automation(Path(directory))
            seed_agentic_data(automation)
            automation.patch_identity = Mock(return_value=False)

            with patch.object(
                agentic_module, "QoderAgenticAutomation", return_value=automation
            ):
                result = agentic_module.reset_agentic_completely()

            self.assertFalse(result)


class AgenticHomeIdentityTests(unittest.TestCase):
    def test_remove_home_identity_clears_installation_id_and_auth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            automation = make_automation(Path(directory))
            seed_agentic_data(automation)
            (automation.home_dir / "memories").mkdir()
            (automation.home_dir / "memories" / "note.md").write_text(
                "keep", encoding="utf-8"
            )

            result = automation.remove_agentic_home_identity()

            home = automation.home_dir
            self.assertTrue(result)
            self.assertFalse((home / "installation_id").exists())
            self.assertFalse((home / ".auth").exists())
            self.assertTrue((home / "memories" / "note.md").exists())

    def test_remove_home_identity_is_true_when_home_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            automation = make_automation(Path(directory))
            automation.home_dir = Path(directory) / "does-not-exist"

            self.assertTrue(automation.remove_agentic_home_identity())


if __name__ == "__main__":
    unittest.main()
