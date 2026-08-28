import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "config/offhost/cloud-infrastructure-offhost-recovery"
SERVICE = ROOT / "config/offhost/cloud-infrastructure-offhost-recovery.service"
TIMER = ROOT / "config/offhost/cloud-infrastructure-offhost-recovery.timer"
README = ROOT / "config/offhost/README.md"


class OffhostRecoveryContract(unittest.TestCase):
    def test_artifacts_exist(self):
        for path in (SCRIPT, SERVICE, TIMER, README):
            self.assertTrue(path.is_file(), str(path))

    def test_script_is_fail_closed_and_allowlisted(self):
        text = SCRIPT.read_text()
        self.assertIn("set -euo pipefail", text)
        self.assertIn("StrictHostKeyChecking=yes", text)
        self.assertIn("BatchMode=yes", text)
        self.assertIn("/gcr/ssh", text)
        self.assertIn("runtime_paths=(", text)
        self.assertNotIn("authorized_keys", text)
        self.assertNotIn("identity.json", text)
        self.assertNotIn("mcf-mission2-terminal.py", text)
        self.assertIn("PRIVATE KEY", text)
        self.assertIn("RESTORE_SMOKE=PASS", text)
        self.assertIn("RECOVERY_P2=PASS", text)

    def test_timer_is_daily_and_persistent(self):
        text = TIMER.read_text()
        self.assertIn("OnCalendar=*-*-* 00:30:00", text)
        self.assertIn("Persistent=true", text)

    def test_service_calls_only_user_script(self):
        text = SERVICE.read_text()
        self.assertIn("Type=oneshot", text)
        self.assertIn("ExecStart=%h/.local/bin/cloud-infrastructure-offhost-recovery", text)
        self.assertIn("NoNewPrivileges=yes", text)


if __name__ == "__main__":
    unittest.main()
