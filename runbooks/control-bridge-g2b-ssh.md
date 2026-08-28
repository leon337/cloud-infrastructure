# Runbook — direct SSH transport for Control Bridge G2-B

Status: **REPOSITORY-ONLY — HUMAN GATE REQUIRED FOR NODE-01**

This transport replaces the GitHub Actions hop with one direct SSH invocation.
It does not change the protected executor, workspace, sudoers policy, or G2-B
operation contract. A separate grant profile binds the real POSIX transport
identity without impersonating the legacy GitHub actor. Nothing in this runbook
authorizes installation, grant issuance, or a real NODE-01 request.

## Fixed boundary

The bootstrap role installs `/usr/local/libexec/mcf-control-g2b-ssh` as
root:root mode `0555`. The adapter itself must run as the existing POSIX account
`ubuntu`. It:

1. accepts exactly one fixed verb: `execute`, `rollback`, `status`, or `revoke`;
2. reads one request object from standard input within 5 seconds and 131072
   bytes, never a transport envelope;
3. rejects caller-supplied `transport_principal` and nested `request` fields;
4. resolves the effective UID and GID through the local password database and
   requires that they exactly match the canonical `ubuntu` account;
5. derives `transport_principal={"login":"ubuntu","actor_id":<ubuntu_uid>}`;
6. invokes only `/usr/bin/sudo -n -u mcf-workspace
   /usr/local/libexec/mcf-control-g2b <fixed-verb>` with `shell=False`, a cleared
   environment, a 60-second timeout, and 8192-byte output limits;
7. validates correlated identifiers, principal, bounded states, canonical UTC
   timestamps, and the complete public result shape before writing one JSON
   object to standard output.

The adapter never accepts login, UID, command path, argv, cwd, environment,
timeout, executor path, grant path, workspace path, or output path from the
caller.

## Explicit SSH grant identity

`issue-control-bridge-g2b-ssh-grant.yml` is the separate HUMAN GATE entrypoint.
On the preflight-verified NODE-01 target it discovers `ubuntu` through the local
password and group databases, requires a non-root numeric UID and matching
canonical primary GID, and writes the grant principal as:

```text
transport_principal_login = ubuntu
transport_principal_id    = <runtime POSIX UID discovered on NODE-01>
```

The adapter independently derives the same `ubuntu/<runtime POSIX UID>` at
request time. A UID alias, changed primary GID, root execution, other account,
caller-supplied principal, or mismatched grant is refused.

The legacy `issue-control-bridge-g2b-grant.yml` invocation retains its default
GitHub profile. The SSH wrapper selects only `ssh-posix-ubuntu`. Both profiles
use the single active pilot grant at `/etc/mcf-control-bridge/g2b-grant.json`, so
they cannot be active simultaneously. Issuance refuses an unrevoked active
grant. After expiry or protocol revocation, LEANDRO may issue a fresh ID; an ID
present in irreversible revocation history can never be reused.

Do not map `ubuntu` to the GitHub actor, accept identity from request JSON, edit
the grant directly, or delete receipts/revocations to switch transports. The
shared POSIX account attributes the local account, not an individual SSH key or
ChatGPT conversation. Restrict and review `authorized_keys` independently.

## Repository validation

From a reviewed, clean checkout:

```bash
python3 -m unittest tests.test_control_bridge_g2b_ssh_adapter -v
python3 -m unittest tests.test_g2b_bootstrap_artifacts -v
cd automation/ansible
ansible-playbook playbooks/apply-control-bridge-g2b.yml --syntax-check
ansible-playbook playbooks/rollback-control-bridge-g2b.yml --syntax-check
ansible-playbook playbooks/issue-control-bridge-g2b-grant.yml --syntax-check
ansible-playbook playbooks/issue-control-bridge-g2b-ssh-grant.yml --syntax-check
```

These checks are repository evidence only. They do not prove installation,
remote SSH execution, grant compatibility, or a real VPS write.

## HUMAN GATE: install and issue the SSH grant

Keep a second authenticated SSH session open. Perform the existing G2-B
precheck and impact review, then run the apply playbook in `--check` mode before
the separately approved installation. Installation never creates or changes a
grant.

Generate exact UTC timestamps 86400 seconds apart and use a new reviewed grant
ID. First preview, then issue through the SSH-specific entrypoint:

```bash
ansible-playbook playbooks/issue-control-bridge-g2b-ssh-grant.yml \
  --check --ask-become-pass --diff \
  -e g2b_grant_id=REPLACE_WITH_FRESH_ID \
  -e g2b_grant_not_before=REPLACE_WITH_UTC_TIMESTAMP \
  -e g2b_grant_not_after=REPLACE_WITH_UTC_TIMESTAMP_PLUS_24H \
  -e g2b_executor_sha256=REPLACE_WITH_REVIEWED_BUNDLE_SHA256

ansible-playbook playbooks/issue-control-bridge-g2b-ssh-grant.yml \
  --ask-become-pass --diff \
  -e g2b_grant_id=REPLACE_WITH_FRESH_ID \
  -e g2b_grant_not_before=REPLACE_WITH_UTC_TIMESTAMP \
  -e g2b_grant_not_after=REPLACE_WITH_UTC_TIMESTAMP_PLUS_24H \
  -e g2b_executor_sha256=REPLACE_WITH_REVIEWED_BUNDLE_SHA256
```

LEANDRO types the sudo credential privately. Never place it in an extra var,
request, log, repository, or chat transcript.

## Direct invocation after separately approved installation and grant

Use a fresh request ID in a private local request file. The file contains only
the Core request, following `control/examples/g2b-ssh-request.example.json`; it
must not contain a `transport` or `transport_principal` object.

The status shape is:

```bash
ssh -T -o BatchMode=yes ubuntu@REVIEWED_NODE_01 \
  /usr/local/libexec/mcf-control-g2b-ssh status \
  < REQUEST.json
```

The remote command and verb are operator-selected fixed strings, not request
data. Use the corresponding fixed verb for an already authorized operation:

```text
workspace.write -> execute
rollback        -> rollback
status          -> status
revoke          -> revoke
```

With an active matching SSH grant, status reaches the unchanged protected
executor. With a missing, expired, revoked, legacy GitHub, or otherwise
mismatched grant, expect a bounded refusal. Do not edit the grant on the VPS to
bypass it.

## Non-goals and emergency handling

This adapter does not create an MCP endpoint, daemon, queue, persistent SSH
session, arbitrary shell, new sudo capability, SSH key, `authorized_keys`
forced command, network listener, firewall rule, systemd unit, or production
authority. It is a one-request transport only.

For revoke, replay, rollback, reissue, emergency stop, and final-state evidence,
use the existing G2-B runbook. Reissue must use a fresh ID and the intended
transport playbook. Do not delete grant, state, receipts, recovery material, or
workspace content to bypass an identity refusal.
