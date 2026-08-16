# Ansible — NODE-01 mission precheck

Mission: `CODEX-EXECUTION-MISSION-001`

This directory contains the first repository-side implementation of the mission's desired-state/recovery contract. The current playbooks are **read-only** and must run before any NODE-01 mutation.

## Security rules

- Never commit an SSH private key, key passphrase, sudo password, token or provider credential.
- Keep Ansible host-key checking enabled.
- Do not accept an unexpected host key automatically.
- Expected canonical ED25519 host fingerprint at mission start:
  `SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`.
- SSH principal remains `ubuntu` unless later canonical state explicitly changes it.
- Privileged precheck uses the existing authenticated sudo policy; use `--ask-become-pass` when running interactively. Do not store the become password in inventory or vars.
- A failed identity/security assertion stops the mutation path and must be recorded as drift/finding.

## 1. Verify the host fingerprint before Ansible

From the secure operator environment that has direct access to NODE-01, inspect the live public host key and compare its fingerprint with the canonical value before proceeding.

Example:

```bash
ssh-keyscan -t ed25519 169.58.171.192 2>/dev/null | ssh-keygen -lf -
```

Expected fingerprint:

```text
SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4
```

If it differs, stop. Do not overwrite `known_hosts` as a workaround.

## 2. Supply the existing private key only at runtime

The example inventory deliberately contains no private-key path. Provide the approved existing key from the secure local environment, for example as an extra var or local inventory override.

Conceptual invocation:

```bash
cd infra/ansible
ANSIBLE_CONFIG=ansible.cfg \
ansible-playbook playbooks/precheck-readonly.yml \
  -e 'ansible_ssh_private_key_file=/secure/local/path/to/approved-existing-key'
```

The key itself never belongs in the repository or command output.

## 3. Run unprivileged read-only precheck

`playbooks/precheck-readonly.yml` verifies/collects:

- hostname/distribution/architecture;
- CPU, RAM, disk and uptime;
- current user/groups;
- interfaces/routes;
- TCP/UDP listeners;
- SSH/fail2ban/backup timer state;
- Docker/Tailscale presence/status if installed;
- `lxd`/`docker` group state.

No task is intended to mutate the host.

## 4. Run privileged read-only security/recovery precheck

Use the same existing key plus interactive sudo authentication:

```bash
cd infra/ansible
ANSIBLE_CONFIG=ansible.cfg \
ansible-playbook playbooks/precheck-privileged-readonly.yml \
  --ask-become-pass \
  -e 'ansible_ssh_private_key_file=/secure/local/path/to/approved-existing-key'
```

It reads:

- effective `sshd -T` policy and asserts the hardened controls expected by the canonical state;
- UFW status;
- effective nftables ruleset;
- listeners;
- fail2ban status;
- config-backup timer and backup-file metadata;
- SHA-256 hashes of selected protected configuration files without printing their contents.

## 5. Evidence handling

Capture sanitized Ansible output under a mission evidence directory only after reviewing it for secrets/sensitive values. Evidence should record:

- timestamp;
- repository/branch/SHA;
- target node;
- host-key verification result;
- assertions PASS/FAIL;
- resource/listener/firewall/service observations;
- detected GitHub↔NODE-01 drift;
- next action/gate.

Do not commit raw logs that expose secrets, authentication material or connection strings.

## 6. Mutation gate

Passing these playbooks does not itself authorize an arbitrary host change. It clears the mission's recovery/reconciliation prerequisite so that the next small, documented slice can execute under Q40-D with its own preconditions and rollback.
