# Foundations automation

This controller-side automation contains no credentials. The dedicated SSH key
path must be supplied through `PLATFORM_SSH_KEY_FILE`; sudo authentication is
entered interactively and is never stored.

Before opening SSH, the controller play validates the dedicated key file and
its recorded public fingerprint. The remote play then pins DEV `node-01` by
inventory address, hostname and a non-reversible machine-id hash. It creates
only a root-only external provenance marker, locked identities, directories,
tmpfiles state and accounting-only systemd slices. It does not install Docker,
start a network listener, change SSH/UFW/XRDP or rotate credentials.

Validation before an authorized apply:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.lock
export PLATFORM_SSH_KEY_FILE=/path/to/dedicated/key
cd automation/ansible
../../.venv/bin/ansible-playbook playbooks/foundation.yml --syntax-check
../../.venv/bin/ansible-playbook playbooks/foundation.yml \
  --ask-become-pass --check --diff
```

The real apply requires LEANDRO to enter the existing sudo password directly:

```bash
../../.venv/bin/ansible-playbook playbooks/foundation.yml \
  --ask-become-pass --diff
```

Rollback is fail-closed: it requires the exact provenance marker, immutable
allowlist, source hashes, empty persistent/runtime directories, no account
process and no slice task. Directories are removed with atomic `rmdir`, never
recursively:

```bash
../../.venv/bin/ansible-playbook playbooks/rollback-foundation.yml \
  --ask-become-pass -e platform_foundation_rollback_confirm=true --diff
```

Never add the password, key, vault material or a connection string to inventory.
Run `scripts/test_foundation_container.sh` only in a disposable VM with its
explicit root-equivalent confirmation gate; the hosted CI is the canonical
integration environment.

## Docker runtime boundary F1.2b

`playbooks/docker-runtime.yml` and `playbooks/rollback-docker-runtime.yml` are
versioned, but both remain blocked on the real node until F1.1 is applied,
reconciled and checkpointed and the same F1.2b commit has green disposable CI.
The controller preflight runs before privilege escalation and accepts only the
recorded DEV identity or the exact GitHub-hosted Ubuntu 24.04 fixture.

The role installs only the five pinned Docker packages after checking the
vendored public key, APT preference, authenticated-index version/path/SHA-256,
daemon JSON and systemd drop-ins. Package-script service start is suppressed;
the explicit start must leave a root-only socket and zero workload state.

Rollback accepts only the exact completed empty slice. It compares both literal
runtime trees to the baseline, freezes device/inode in a removal manifest and
removes exact leaves bottom-up. It never uses recursive removal or autoremove;
the external marker is removed last. An incomplete transaction is preserved for
classification rather than resumed automatically.

The only currently recorded local execution is static/non-privileged:

```bash
scripts/test.sh
cd automation/ansible
ansible-playbook playbooks/docker-runtime.yml --syntax-check
ansible-playbook playbooks/rollback-docker-runtime.yml --syntax-check
```

Do not run either Docker playbook against `inventory/dev` or real localhost
while the documented gates remain pending. The privileged lifecycle belongs
only to `scripts/test_docker_boundary_vm.sh` on its immutable disposable CI VM.
