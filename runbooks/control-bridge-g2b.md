# Runbook — protected Control Bridge G2-B bootstrap and grant lifecycle

Status: **HUMAN GATE REQUIRED — do not run on NODE-01 without review**

This runbook installs the reviewed G2-B bundle but keeps installation separate
from delegated authority. The apply role never creates, renews, or replaces a
grant. Only the grant playbook may do that, from four explicit human values.

## Impact and non-goals

The bootstrap creates one locked `mcf-workspace` identity, root-owned protected
parents, one protected rebuildable smoke workspace, immutable executor files,
four exact sudo transitions, tmpfiles state, and a provenance marker. Grant
issuance later creates one non-secret root-owned 24-hour JSON file.

Non-goals are arbitrary shell, root normal execution, Docker or Docker socket
access, package changes, production, SSH/UFW/network/systemd changes, secret
management, Git mutation, or any change to the frozen F1.2c worktree/state. The
legacy `/home/ubuntu/mcf-workspaces` fixture is observed but never changed.

## Precheck and required second SSH session

1. Review the exact candidate SHA and this runbook from a clean checkout.
2. Confirm the G1/G2-A read-only probes, runner identity, protected-path
   absence, legacy-fixture preservation, and NODE-01 hostname/machine guards.
3. Open a **second SSH session** to NODE-01 and keep it open for recovery.
4. In that recovery session, enter the sudo credential directly with
   `sudo -v`. Never put it in a variable, command argument, file, chat, log, or
   GitHub field.
5. Confirm the runner is idle and no G2-B operation or installation lock exists.

On the reviewed controller checkout:

```bash
export PLATFORM_SSH_KEY_FILE='<dedicated-reviewed-key-path>'
cd automation/ansible
ansible-playbook playbooks/apply-control-bridge-g2b.yml --syntax-check
ansible-playbook playbooks/rollback-control-bridge-g2b.yml --syntax-check
ansible-playbook playbooks/issue-control-bridge-g2b-grant.yml --syntax-check
ansible-playbook playbooks/apply-control-bridge-g2b.yml --check --ask-become-pass --diff
```

Abort on an identity mismatch, unmanaged path, symlink, hash drift, existing
unmarked account/grant/lock, unexpected protected-tree entry, or check failure.

## Apply and idempotence

LEANDRO runs the install only after the exact candidate is approved:

```bash
ansible-playbook playbooks/apply-control-bridge-g2b.yml --ask-become-pass --diff
ansible-playbook playbooks/apply-control-bridge-g2b.yml --ask-become-pass --diff
```

The second run is the idempotence proof. It must report no changed desired-state
object. The role's status probe may return `grant_missing` because apply does
not authorize mutation.

Before issuing a grant, verify the direct boundary from the recovery SSH
session. The JSON request ID below is a placeholder and must be replaced with a
fresh reviewed non-live check ID:

```bash
printf '%s\n' '{"transport_principal":{"login":"leon337","actor_id":REPLACE_WITH_REVIEWED_NUMERIC_ACTOR_ID},"request":{"protocol":"MCF_WORKSPACE_MUTATION_V1","request_id":"REPLACE-WITH-FRESH-STATUS-ID","mission_id":"CONTROL-BRIDGE-G2B-PILOT","declared_actor":"MESTRE_MCF","project":{"tenant":"leon337","name":"g2a-smoke","environment":"dev"},"operation":"status","arguments":{}}}' | sudo -n -u mcf-workspace /usr/local/libexec/mcf-control-g2b status
```

`ubuntu` must still be denied direct write to
`/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev`.

## UTC timestamp generation and grant issuance

Generate timestamps immediately before the human issuance step. They must be
UTC and exactly 86400 seconds apart. Use a fresh placeholder-derived grant ID;
never copy an ID from evidence or this document.

```bash
GRANT_ID='REPLACE-WITH-FRESH-GRANT-ID'
NOT_BEFORE="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
NOT_AFTER="$(date -u -d "$NOT_BEFORE + 24 hours" '+%Y-%m-%dT%H:%M:%SZ')"
EXECUTOR_SHA256='7ed806ee4d73743f3d0ab6f7f5c216494ed0d4f645f5f2bea0b128f2a689d3af'
ansible-playbook playbooks/issue-control-bridge-g2b-grant.yml \
  --ask-become-pass --diff \
  -e "g2b_grant_id=$GRANT_ID" \
  -e "g2b_grant_not_before=$NOT_BEFORE" \
  -e "g2b_grant_not_after=$NOT_AFTER" \
  -e "g2b_executor_sha256=$EXECUTOR_SHA256"
```

The playbook refuses an active grant and every revoked grant ID. Reissue uses a
new explicit ID and new human timestamps; it never silently extends authority.

## Acceptance sequence

Run and record safe identifiers, timestamps, status/error codes, modes, and
hashes only, in this exact order:

1. fresh G1/G2-A read and runner status;
2. protected target absent and transport direct-write denial;
3. grant active for exactly 24 hours;
4. authorized write;
5. G2-A expected safe hash read;
6. identical request replay without a second mutation;
7. changed request under the same ID returns conflict;
8. concurrency is serialized or refused;
9. local receipt and GitHub result correlate;
10. protocol rollback removes the pilot file;
11. G2-A confirms the restored final state;
12. revoke succeeds;
13. post-revoke write is refused;
14. LEANDRO performs explicit reissue with a fresh ID;
15. MESTRE/MCF performs one authorized bounded operation through the reissued
    channel and restores the pilot state again.

Do not capture request content, prior bytes, credentials, environment dumps, or
unrelated NODE-01 state.

## Revoke, reissue, and emergency stop

Normal revocation uses the exact `revoke` executor verb and its reviewed JSON
request. Reissue follows the timestamp and grant command above with a fresh ID.

For an **emergency stop**, use the retained second SSH session. Stop new
transitions by moving only `/etc/sudoers.d/mcf-control-g2b` to a root-owned
disabled filename, validate the remaining sudo policy with `visudo -cf`, and
preserve the grant, state, audit, workspace, and marker for diagnosis. Do not
delete state or improvise a recursive cleanup. Runner service stop or label
removal is an additional transport stop, not a substitute for revocation.

## Bounded bootstrap rollback gates

Bootstrap rollback is permitted only after protocol rollback restored the
pilot path and the grant is absent, expired, or revoked. The playbook then
requires exact marker and installed hashes, no active mutation or snapshot, no
unresolved receipt, an absent pilot file, no service-account process or open
file, and only exact protected-tree baseline entries.

Preview and execute only after those gates are independently reviewed:

```bash
ansible-playbook playbooks/rollback-control-bridge-g2b.yml \
  --check --ask-become-pass --diff \
  -e g2b_rollback_confirm=true
ansible-playbook playbooks/rollback-control-bridge-g2b.yml \
  --ask-become-pass --diff \
  -e g2b_rollback_confirm=true
```

Rollback removes validated leaf files and exact empty directories only. It
does not recurse, glob across parents, remove a home, uninstall packages, or
touch the legacy fixture. The provenance marker is removed last.
