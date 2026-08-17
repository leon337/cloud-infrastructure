from __future__ import annotations

import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap_mission_001_autonomous_runner.sh"


def heredoc(text: str, name: str, terminator: str) -> str:
    match = re.search(
        rf"cat >\"\$workdir/{re.escape(name)}\" <<'?{terminator}'?\n(.*?)\n{terminator}\n",
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise AssertionError(f"missing {name} heredoc")
    return match.group(1)


class TemporaryAutonomousRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.runner = heredoc(cls.bootstrap, "runner", "RUNNER")
        cls.sudoers = heredoc(cls.bootstrap, "sudoers", "SUDOERS")
        cls.revoke = heredoc(cls.bootstrap, "revoke", "REVOKE")

    def test_sudoers_allows_only_six_exact_runner_invocations(self):
        expected = {
            "check",
            "apply",
            "test",
            "reconcile",
            "rollback",
            "status",
        }
        actual = set(
            re.findall(
                r"/usr/local/sbin/codex-mission-001-runner ([a-z]+)",
                self.sudoers,
            )
        )
        self.assertEqual(actual, expected)
        self.assertEqual(self.sudoers.count("codex-mission-001-runner "), 6)
        self.assertIn(
            "ubuntu ALL=(root) NOPASSWD: NOSETENV: CODEX_MISSION_001_TEMP",
            self.sudoers,
        )
        self.assertNotRegex(self.sudoers, r"ALL=\(ALL(?::ALL)?\).*NOPASSWD")
        self.assertNotIn("/bin/sh", self.sudoers)
        self.assertNotIn("/bin/bash", self.sudoers)

    def test_runner_rejects_extra_or_unlisted_arguments(self):
        self.assertIn("[[ $# -eq 1 ]]", self.runner)
        self.assertIn("operation_not_allowlisted", self.runner)
        self.assertIn(
            "ALLOWED_OPERATIONS='check apply test reconcile rollback status'",
            self.runner,
        )
        self.assertNotIn("eval ", self.runner)
        self.assertNotIn("bash -c", self.runner)
        self.assertNotIn("sh -c", self.runner)

    def test_privileged_entrypoints_are_fixed_root_owned_and_argument_free(self):
        self.assertIn(
            'entrypoint="$REPO_ROOT/automation/mission-001/operations/$operation"',
            self.runner,
        )
        self.assertIn("root:root:755:1", self.runner)
        self.assertRegex(self.runner, r'\n    "\$entrypoint"\n')

    def test_audit_record_has_all_required_fields(self):
        audit = "timestamp=%s operation=%s git_sha=%s result=%s"
        self.assertIn(audit, self.runner)
        self.assertIn("logger -t codex-mission-001", self.runner)
        self.assertIn("operation=bootstrap git_sha=%s result=PASS", self.bootstrap)
        self.assertIn("operation=automatic-revoke", self.revoke)

    def test_expiry_is_exactly_twelve_hours_and_self_revokes(self):
        self.assertIn("+ 43200", self.bootstrap)
        self.assertNotIn("+ 5400", self.bootstrap)
        self.assertIn("after 12 hours", self.bootstrap)
        self.assertNotIn("after 90 minutes", self.bootstrap)
        self.assertIn("OnCalendar=$expires_calendar", self.bootstrap)
        self.assertIn('rm -f -- "$SUDOERS_PATH"', self.runner)
        self.assertIn('rm -f -- "$SUDOERS_PATH"', self.revoke)
        self.assertIn("Persistent=true", self.bootstrap)

    def test_sudoers_is_validated_before_and_after_install(self):
        generated_validation = self.bootstrap.index(
            'visudo -cf "$workdir/sudoers"'
        )
        sudoers_install = self.bootstrap.index(
            'install -o root -g root -m 0440 "$workdir/sudoers"'
        )
        global_validation = self.bootstrap.index(
            "visudo -cf /etc/sudoers", sudoers_install
        )
        self.assertLess(generated_validation, sudoers_install)
        self.assertGreater(global_validation, sudoers_install)

    def test_snapshot_and_authorization_are_root_owned_and_fail_closed(self):
        self.assertIn("readonly REPO_ROOT=/opt/codex-mission-001/repository", self.runner)
        self.assertIn('chown -R root:root "$REPO_ROOT"', self.bootstrap)
        self.assertIn("bootstrap_complete=false", self.bootstrap)
        self.assertIn('rm -f -- "$SUDOERS_PATH"', self.bootstrap)
        self.assertIn("production_guard_true", self.bootstrap)
        self.assertIn("DEFERRED_BY_HUMAN_DECISION", self.runner)

    def test_production_guards_match_the_canonical_current_state(self):
        current = (ROOT / "state" / "current.yaml").read_text(encoding="utf-8")
        self.assertRegex(
            current,
            r"(?m)^\s*production_promotion_authorized:\s+false$",
        )
        self.assertRegex(
            current,
            r"(?m)^\s*production_promotion:\s+NOT_AUTHORIZED_HUMAN_GATE_REQUIRED$",
        )
        self.assertIn("production_promotion_authorized:[[:space:]]+false", self.bootstrap)
        self.assertIn(
            "production_promotion:[[:space:]]+NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
            self.bootstrap,
        )

    def test_reconcile_requires_a_namespaced_controller_signature(self):
        self.assertIn("ssh-keygen -Y verify", self.bootstrap)
        self.assertIn("ssh-keygen -Y verify", self.runner)
        self.assertIn("readonly SIGNING_NAMESPACE=codex-mission-001", self.runner)
        self.assertIn("readonly SIGNING_IDENTITY=mission-001-controller", self.runner)
        self.assertIn("repository.bundle.sig", self.runner)
        self.assertIn("root:root:600:1", self.runner)

    def test_bundle_verification_uses_an_explicit_bare_repository(self):
        self.assertIn('git init --bare --quiet "$workdir/verify.git"', self.bootstrap)
        self.assertIn(
            'git -C "$workdir/verify.git" bundle verify "$SOURCE_BUNDLE"',
            self.bootstrap,
        )
        self.assertIn('git init --bare --quiet "$staging/verify.git"', self.runner)
        self.assertIn(
            'git -C "$staging/verify.git" bundle verify "$INBOX_BUNDLE"',
            self.runner,
        )

    def test_missing_libexec_parent_is_created_and_failure_cleanup_is_bounded(self):
        self.assertIn("libexec_created=false", self.bootstrap)
        self.assertIn(
            "install -d -o root -g root -m 0755 /usr/local/libexec",
            self.bootstrap,
        )

    def test_inbox_parent_allows_only_ubuntu_traversal(self):
        self.assertIn(
            'install -d -o root -g ubuntu -m 0710 "$STATE_ROOT"',
            self.bootstrap,
        )
        self.assertIn(
            'install -d -o ubuntu -g ubuntu -m 0700 "$STATE_ROOT/inbox"',
            self.bootstrap,
        )
        self.assertIn(
            "if [[ $libexec_created == true ]]; then rmdir /usr/local/libexec",
            self.bootstrap,
        )

    def test_bootstrap_does_not_mutate_access_or_recovery_services(self):
        forbidden = re.compile(
            r"systemctl\s+(?:stop|disable|mask|restart)\s+[^\n]*(?:ssh|ufw|xrdp|fail2ban|lxd)",
            flags=re.IGNORECASE,
        )
        self.assertIsNone(forbidden.search(self.bootstrap))
        self.assertNotRegex(self.bootstrap, r"(?m)^\s*ufw\s")
        self.assertNotIn("sshd_config", self.bootstrap)
        self.assertNotIn("credential rotation", self.bootstrap.lower())

    def test_status_and_check_fail_explicitly_on_forbidden_runtime_state(self):
        self.assertIn(
            "if systemctl is-active --quiet snap.lxd.daemon.service; then return 1; fi",
            self.runner,
        )
        self.assertIn("if ip -o link show", self.runner)
        self.assertIn("if ss -Hlnptu", self.runner)

    def test_unprivileged_tests_use_only_a_private_ephemeral_snapshot(self):
        self.assertIn("mktemp -d /run/codex-mission-001-test.XXXXXX", self.runner)
        self.assertIn('cp -a -- "$REPO_ROOT/." "$test_root/"', self.runner)
        self.assertIn('chown -R ubuntu:ubuntu "$test_root"', self.runner)
        self.assertIn('chmod -R u+rwX,go-rwx "$test_root"', self.runner)
        self.assertIn('rm -rf --one-file-system "$test_root"', self.runner)
        self.assertIn("GIT_CONFIG_COUNT=1", self.runner)
        self.assertIn("GIT_CONFIG_KEY_0=safe.directory", self.runner)
        self.assertIn('GIT_CONFIG_VALUE_0="$test_root"', self.runner)
        self.assertNotIn("safe.directory '*'", self.runner)

    def test_reviewed_apply_updates_only_the_exact_known_runner(self):
        operation = (
            ROOT / "automation" / "mission-001" / "operations" / "apply"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "OLD_RUNNER_SHA256=36945487cd448a76f75a5bc8761a7d46547ae148acdcc9aed0ab3af768571d7d",
            operation,
        )
        self.assertIn(
            "DESIRED_RUNNER_SHA256=c388e8cb3b37e08d5cffe86f3330fe1f207af6c150e9e1f80b5f185ebadd3645",
            operation,
        )
        self.assertIn("install -o root -g root -m 0755", operation)
        self.assertNotIn("systemctl", operation)
        self.assertNotIn("/etc/sudoers", operation)
        self.assertNotIn("docker", operation.lower())

    def test_reconcile_normalizes_signed_snapshot_readability(self):
        self.assertEqual(self.bootstrap.count('chmod -R a+rX,go-w "$REPO_ROOT"'), 1)
        self.assertEqual(
            self.runner.count('chmod -R a+rX,go-w "$staging/repository"'),
            1,
        )

    def test_privileged_git_checks_do_not_rewrite_the_index(self):
        self.assertIn("export GIT_OPTIONAL_LOCKS=0", self.runner)

    def test_no_password_capture_or_persistence_mechanism_exists(self):
        lowered = self.bootstrap.lower()
        for forbidden in (
            "sshpass",
            "sudo -s",
            "sudo -i",
            "askpass",
            "password=",
            "passwd -",
        ):
            self.assertNotIn(forbidden, lowered)


if __name__ == "__main__":
    unittest.main()
