# Local KVM Disposable Integration Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a zero-additional-cost, fail-closed Ubuntu 24.04 QEMU/KVM laboratory on the operator workstation that executes the exact F1.2c privileged Docker/systemd/iptables integration lifecycle on a disposable VM and emits durable non-secret evidence.

**Architecture:** A host-side launcher runs without host `sudo`, verifies a pinned official Ubuntu 24.04 amd64 cloud image, creates an ephemeral qcow2 overlay plus cloud-init seed, starts QEMU/KVM with user-mode networking and localhost-only SSH forwarding, bundles the exact clean Git candidate, transfers it into the guest, and invokes the existing NODE-01 network-services harness through a distinct local-KVM authorization gate. The guest carries all privileged operations; the workstation remains only the hypervisor, and NODE-01 is never used as the disposable test environment.

**Tech Stack:** Bash, Python `unittest` for static contract tests, QEMU/KVM, qcow2, cloud-init (`cloud-localds`), OpenSSH/SCP, Git bundle, Ubuntu 24.04 LTS cloud image, Docker Engine inside the guest, systemd, iptables/ip6tables.

**Spec:** `docs/superpowers/specs/2026-08-19-local-kvm-disposable-lab-design.md`

## Global Constraints

- Target guest: official Ubuntu 24.04 LTS amd64 released cloud image.
- Pinned image URL: `https://cloud-images.ubuntu.com/releases/noble/release-20260814/ubuntu-24.04-server-cloudimg-amd64.img`.
- Pinned image SHA-256: `6e40c07ae715f744f84af0bec76415cc1987dd115b4b8de437818561f01a3733`.
- Normal host execution requires no `sudo`.
- QEMU networking is user-mode only; no TAP, bridge, macvtap, host network namespace, host iptables, or host Docker socket is allowed.
- SSH forwarding must bind only to `127.0.0.1`.
- Candidate input is exactly one SHA argument; no arbitrary guest command argument is permitted.
- Guest authentication uses a per-run ephemeral SSH key; password login is disabled.
- Guest receives no GitHub token, VPS key, operator private key, production secret, or reusable credential.
- The existing GitHub-hosted disposable confirmation gate remains valid; local KVM is added as a second explicit gate rather than weakening the first.
- Any missing identity, provenance, image, capacity, candidate, or cleanup invariant fails closed before privileged guest integration begins.
- Guest defaults: 2 vCPU, 4 GiB RAM, 24 GiB virtual disk, headless QEMU.
- Durable evidence contains only non-secret metadata and sanitized test output.
- Full KVM integration runs only on the operator workstation; the existing NODE-01 self-hosted runner may execute static tests only.

---

## File Structure

- Create `platform/kvm/f1-2c-ubuntu-24.04-amd64.env` — immutable cloud-image URL, filename, and SHA-256 provenance constants.
- Create `platform/kvm/f1-2c-cloud-init-user-data.yaml.in` — cloud-init template for the ephemeral `mcf-lab` administrator, SSH key injection, lab marker, packages, Docker startup, and password-login prohibition.
- Create `platform/kvm/f1-2c-cloud-init-meta-data.yaml.in` — metadata template containing the unique KVM-lab instance ID and hostname.
- Create `scripts/run_f1_2c_kvm_lab.sh` — narrow host-side orchestrator; performs preflight, image cache verification/download, VM creation, SSH readiness, Git bundle transfer, guest invocation, evidence persistence, and bounded cleanup.
- Modify `scripts/test_node_network_services_vm.sh` — preserve the GitHub-hosted gate and add a distinct local-KVM gate, then use the same privileged lifecycle for both accepted disposable environments.
- Create `tests/test_local_kvm_lab.py` — static fail-closed tests for launcher, templates, image pinning, networking, candidate handling, cleanup, and guest gate.
- Modify `tests/test_node_network_services.py` — extend the existing disposable-harness contract to require both explicit identities without weakening the GitHub-hosted path.
- Optionally modify `.gitignore` only if implementation creates repository-local transient artifacts; preferred design keeps cache/evidence outside the repository so no ignore change is needed.

---

### Task 1: Pin image provenance and establish the host launcher security contract

**Files:**
- Create: `platform/kvm/f1-2c-ubuntu-24.04-amd64.env`
- Create: `tests/test_local_kvm_lab.py`
- Create: `scripts/run_f1_2c_kvm_lab.sh`

**Interfaces:**
- Consumes: repository root, one positional candidate SHA.
- Produces: `scripts/run_f1_2c_kvm_lab.sh <40-hex-candidate-sha>`; exits non-zero with `KVM_LAB_REFUSED reason=<reason>` before mutation when a preflight invariant fails.

- [ ] **Step 1: Write failing provenance and fixed-CLI tests**

Add tests that read the files as text and require the exact pin plus a one-argument CLI:

```python
from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/run_f1_2c_kvm_lab.sh"
IMAGE_ENV = ROOT / "platform/kvm/f1-2c-ubuntu-24.04-amd64.env"


class LocalKvmLabTests(unittest.TestCase):
    def test_image_is_release_pinned_by_url_and_sha256(self):
        text = IMAGE_ENV.read_text()
        self.assertIn(
            "MCF_KVM_IMAGE_URL=https://cloud-images.ubuntu.com/releases/noble/release-20260814/ubuntu-24.04-server-cloudimg-amd64.img",
            text,
        )
        self.assertIn(
            "MCF_KVM_IMAGE_SHA256=6e40c07ae715f744f84af0bec76415cc1987dd115b4b8de437818561f01a3733",
            text,
        )
        self.assertNotIn("/current/", text)

    def test_launcher_has_one_fixed_candidate_argument_and_no_arbitrary_command(self):
        text = LAUNCHER.read_text()
        self.assertIn("[[ $# -eq 1 ]] || refuse exactly_one_candidate_sha_required", text)
        self.assertIn("[[ $1 =~ ^[0-9a-f]{40}$ ]] || refuse invalid_candidate_sha", text)
        self.assertNotIn("eval ", text)
        self.assertNotIn('bash -c "$', text)
```

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest -v \
  tests.test_local_kvm_lab.LocalKvmLabTests.test_image_is_release_pinned_by_url_and_sha256 \
  tests.test_local_kvm_lab.LocalKvmLabTests.test_launcher_has_one_fixed_candidate_argument_and_no_arbitrary_command
```

Expected: FAIL because the provenance file and launcher do not yet exist.

- [ ] **Step 3: Add the immutable image manifest**

Create `platform/kvm/f1-2c-ubuntu-24.04-amd64.env` exactly as:

```bash
MCF_KVM_IMAGE_NAME=ubuntu-24.04-server-cloudimg-amd64.img
MCF_KVM_IMAGE_URL=https://cloud-images.ubuntu.com/releases/noble/release-20260814/ubuntu-24.04-server-cloudimg-amd64.img
MCF_KVM_IMAGE_SHA256=6e40c07ae715f744f84af0bec76415cc1987dd115b4b8de437818561f01a3733
```

- [ ] **Step 4: Add the minimal fail-closed launcher skeleton**

Create `scripts/run_f1_2c_kvm_lab.sh` with strict mode, repository-root discovery, one SHA argument, `refuse()`, and source only the fixed provenance file:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly IMAGE_ENV="$ROOT/platform/kvm/f1-2c-ubuntu-24.04-amd64.env"

refuse() { printf 'KVM_LAB_REFUSED reason=%s\n' "$1" >&2; exit 2; }

[[ $# -eq 1 ]] || refuse exactly_one_candidate_sha_required
[[ $1 =~ ^[0-9a-f]{40}$ ]] || refuse invalid_candidate_sha
readonly CANDIDATE_SHA=$1

# shellcheck disable=SC1090
source "$IMAGE_ENV"

printf 'KVM_LAB_PREFLIGHT=PASS candidate=%s\n' "$CANDIDATE_SHA"
```

- [ ] **Step 5: Run focused tests and verify GREEN**

Run the Step 2 command again. Expected: PASS.

- [ ] **Step 6: Commit Task 1**

```bash
git add platform/kvm/f1-2c-ubuntu-24.04-amd64.env tests/test_local_kvm_lab.py scripts/run_f1_2c_kvm_lab.sh
git commit -m "test(f1.2c): establish local KVM lab contract"
```

---

### Task 2: Implement host preflight, candidate integrity, image cache verification, and bounded run directories

**Files:**
- Modify: `tests/test_local_kvm_lab.py`
- Modify: `scripts/run_f1_2c_kvm_lab.sh`

**Interfaces:**
- Consumes: candidate SHA, `/dev/kvm`, local clean Git checkout, standard host tools.
- Produces: verified immutable base image at `${XDG_CACHE_HOME:-$HOME/.cache}/mcf-kvm-lab/<image-name>`; unique run directory below `${TMPDIR:-/tmp}`; persistent evidence root `${XDG_STATE_HOME:-$HOME/.local/state}/mcf-kvm-lab/evidence`.

- [ ] **Step 1: Write failing host-boundary tests**

Add tests asserting the launcher requires `qemu-system-x86_64`, `qemu-img`, `cloud-localds`, `ssh`, `scp`, `ssh-keygen`, `git`, `curl`, and `sha256sum`; checks `/dev/kvm`; rejects NODE-01; requires exact HEAD and clean status; never invokes host `sudo`, `docker`, `iptables`, TAP, or bridge commands; and constrains cleanup to a launcher-created prefix.

Representative assertions:

```python
def test_host_preflight_is_fail_closed_and_unprivileged(self):
    text = LAUNCHER.read_text()
    for command in (
        "qemu-system-x86_64", "qemu-img", "cloud-localds", "ssh", "scp",
        "ssh-keygen", "git", "curl", "sha256sum",
    ):
        self.assertIn(command, text)
    self.assertIn("/dev/kvm", text)
    self.assertIn("vmi3506102", text)
    self.assertIn("node-01", text)
    self.assertIn("git status --porcelain", text)
    self.assertNotRegex(text, r"(?m)^\s*sudo\b")
    self.assertNotRegex(text, r"(?m)^\s*(iptables|ip6tables|docker)\b")
    self.assertNotIn("-netdev tap", text)
    self.assertNotIn("brctl", text)
```

- [ ] **Step 2: Run focused tests and verify RED**

```bash
python3 -m unittest -v tests.test_local_kvm_lab.LocalKvmLabTests.test_host_preflight_is_fail_closed_and_unprivileged
```

Expected: FAIL because those guards are not implemented.

- [ ] **Step 3: Implement prerequisite and host identity checks**

Add fixed preflight functions:

```bash
require_command() {
  command -v "$1" >/dev/null 2>&1 || refuse "missing_command_$1"
}

for command in qemu-system-x86_64 qemu-img cloud-localds ssh scp ssh-keygen git curl sha256sum; do
  require_command "$command"
done

case "$(hostname --short)" in
  node-01 | vmi3506102) refuse real_dev_node ;;
esac

[[ -c /dev/kvm && -r /dev/kvm && -w /dev/kvm ]] || refuse kvm_access_unavailable
[[ $(git -C "$ROOT" rev-parse HEAD) == "$CANDIDATE_SHA" ]] || refuse candidate_not_head
[[ -z $(git -C "$ROOT" status --porcelain) ]] || refuse repository_not_clean
```

- [ ] **Step 4: Implement cache and SHA-256 verification**

Use a user-owned cache only. Existing files with the wrong digest are refused, not silently trusted. Downloads go to a temporary sibling then atomically rename after verification:

```bash
readonly CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/mcf-kvm-lab"
readonly BASE_IMAGE="$CACHE_DIR/$MCF_KVM_IMAGE_NAME"
mkdir -p -m 0700 "$CACHE_DIR"

verify_image() {
  printf '%s  %s\n' "$MCF_KVM_IMAGE_SHA256" "$1" | sha256sum --check --status
}

if [[ -e $BASE_IMAGE ]]; then
  [[ -f $BASE_IMAGE && ! -L $BASE_IMAGE ]] || refuse invalid_cached_image_type
  verify_image "$BASE_IMAGE" || refuse cached_image_digest_mismatch
else
  download="$CACHE_DIR/.${MCF_KVM_IMAGE_NAME}.$$"
  trap 'rm -f -- "$download"' RETURN
  curl --fail --location --proto '=https' --tlsv1.2 --output "$download" "$MCF_KVM_IMAGE_URL"
  verify_image "$download" || refuse downloaded_image_digest_mismatch
  chmod 0600 "$download"
  mv -- "$download" "$BASE_IMAGE"
  trap - RETURN
fi
```

- [ ] **Step 5: Implement bounded temporary and evidence directories**

Use launcher-created locations only:

```bash
readonly RUN_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/mcf-f1-2c-kvm.XXXXXXXX")
readonly EVIDENCE_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/mcf-kvm-lab/evidence"
readonly EVIDENCE_DIR="$EVIDENCE_ROOT/$(date -u +%Y%m%dT%H%M%SZ)-${CANDIDATE_SHA:0:12}"
mkdir -p -m 0700 "$EVIDENCE_DIR"

cleanup() {
  case $RUN_ROOT in
    "${TMPDIR:-/tmp}"/mcf-f1-2c-kvm.*) ;;
    *) printf '%s\n' 'KVM_LAB_CLEANUP_REFUSED invalid_run_root' >&2; return 1 ;;
  esac
  # QEMU-specific cleanup is added in Task 4.
  rm -f -- "$RUN_ROOT"/candidate.bundle "$RUN_ROOT"/seed.img "$RUN_ROOT"/overlay.qcow2 \
    "$RUN_ROOT"/id_ed25519 "$RUN_ROOT"/id_ed25519.pub "$RUN_ROOT"/qemu.pid
  rmdir -- "$RUN_ROOT" 2>/dev/null || true
}
trap cleanup EXIT INT TERM HUP
```

- [ ] **Step 6: Run focused tests and full static suite**

```bash
python3 -m unittest -v tests.test_local_kvm_lab
PYTHON=python3 REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=0 scripts/test.sh
```

Expected: all new tests PASS; complete static suite PASS.

- [ ] **Step 7: Commit Task 2**

```bash
git add scripts/run_f1_2c_kvm_lab.sh tests/test_local_kvm_lab.py
git commit -m "feat(f1.2c): add fail-closed KVM host preflight"
```

---

### Task 3: Add cloud-init guest identity, ephemeral admin account, and secret-free bootstrap

**Files:**
- Create: `platform/kvm/f1-2c-cloud-init-user-data.yaml.in`
- Create: `platform/kvm/f1-2c-cloud-init-meta-data.yaml.in`
- Modify: `tests/test_local_kvm_lab.py`
- Modify: `scripts/run_f1_2c_kvm_lab.sh`

**Interfaces:**
- Consumes: per-run SSH public key and random lab ID generated by the launcher.
- Produces: seed image with guest hostname `mcf-f1-2c-kvm-<12-hex-run-id>`, user `mcf-lab`, marker `/etc/mcf-f1-2c-kvm-lab`, Docker installed/enabled, password SSH disabled.

- [ ] **Step 1: Write failing template/security tests**

Require exact markers and prohibit reusable credentials:

```python
def test_cloud_init_creates_only_ephemeral_lab_identity(self):
    user_data = (ROOT / "platform/kvm/f1-2c-cloud-init-user-data.yaml.in").read_text()
    meta = (ROOT / "platform/kvm/f1-2c-cloud-init-meta-data.yaml.in").read_text()
    self.assertIn("name: mcf-lab", user_data)
    self.assertIn("sudo: ALL=(ALL) NOPASSWD:ALL", user_data)
    self.assertIn("ssh_pwauth: false", user_data)
    self.assertIn("__MCF_KVM_SSH_PUBLIC_KEY__", user_data)
    self.assertIn("/etc/mcf-f1-2c-kvm-lab", user_data)
    self.assertIn("MCF_F1_2C_KVM_LAB_V1", user_data)
    self.assertIn("docker.io", user_data)
    self.assertIn("hostname: mcf-f1-2c-kvm-__MCF_KVM_RUN_ID__", meta)
    self.assertNotIn("github_pat_", user_data)
    self.assertNotIn("BEGIN OPENSSH PRIVATE KEY", user_data)
```

- [ ] **Step 2: Run test and verify RED**

```bash
python3 -m unittest -v tests.test_local_kvm_lab.LocalKvmLabTests.test_cloud_init_creates_only_ephemeral_lab_identity
```

Expected: FAIL because templates do not exist.

- [ ] **Step 3: Create user-data template**

Use this shape:

```yaml
#cloud-config
ssh_pwauth: false
disable_root: true
users:
  - default
  - name: mcf-lab
    gecos: MCF disposable KVM laboratory
    groups: [adm, sudo]
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: true
    ssh_authorized_keys:
      - __MCF_KVM_SSH_PUBLIC_KEY__
packages:
  - docker.io
  - git
  - curl
  - ca-certificates
  - iptables
  - dnsutils
write_files:
  - path: /etc/mcf-f1-2c-kvm-lab
    owner: root:root
    permissions: '0400'
    content: |
      MCF_F1_2C_KVM_LAB_V1
      run_id=__MCF_KVM_RUN_ID__
runcmd:
  - [systemctl, enable, --now, docker.service]
```

- [ ] **Step 4: Create metadata template**

```yaml
instance-id: mcf-f1-2c-kvm-__MCF_KVM_RUN_ID__
local-hostname: mcf-f1-2c-kvm-__MCF_KVM_RUN_ID__
hostname: mcf-f1-2c-kvm-__MCF_KVM_RUN_ID__
```

- [ ] **Step 5: Render templates and generate a cloud-init seed**

In the launcher, create a 12-hex run ID, generate an Ed25519 key without passphrase because the key itself is ephemeral and mode 0600, substitute only the exact public-key/run-id tokens, then call `cloud-localds`:

```bash
readonly RUN_ID=$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')
readonly GUEST_HOSTNAME="mcf-f1-2c-kvm-$RUN_ID"
readonly SSH_KEY="$RUN_ROOT/id_ed25519"
ssh-keygen -q -t ed25519 -N '' -f "$SSH_KEY"
chmod 0600 "$SSH_KEY"

ssh_pub=$(<"$SSH_KEY.pub")
sed \
  -e "s|__MCF_KVM_RUN_ID__|$RUN_ID|g" \
  -e "s|__MCF_KVM_SSH_PUBLIC_KEY__|$ssh_pub|g" \
  "$ROOT/platform/kvm/f1-2c-cloud-init-user-data.yaml.in" >"$RUN_ROOT/user-data"
sed "s|__MCF_KVM_RUN_ID__|$RUN_ID|g" \
  "$ROOT/platform/kvm/f1-2c-cloud-init-meta-data.yaml.in" >"$RUN_ROOT/meta-data"
cloud-localds "$RUN_ROOT/seed.img" "$RUN_ROOT/user-data" "$RUN_ROOT/meta-data"
```

- [ ] **Step 6: Run focused tests and full static suite**

```bash
python3 -m unittest -v tests.test_local_kvm_lab
PYTHON=python3 REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=0 scripts/test.sh
```

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

```bash
git add platform/kvm/f1-2c-cloud-init-user-data.yaml.in \
  platform/kvm/f1-2c-cloud-init-meta-data.yaml.in \
  scripts/run_f1_2c_kvm_lab.sh tests/test_local_kvm_lab.py
git commit -m "feat(f1.2c): define disposable KVM guest identity"
```

---

### Task 4: Create and boot the disposable QEMU/KVM VM using host-safe networking

**Files:**
- Modify: `tests/test_local_kvm_lab.py`
- Modify: `scripts/run_f1_2c_kvm_lab.sh`

**Interfaces:**
- Consumes: verified base image, seed image, ephemeral SSH key.
- Produces: running KVM guest reachable only through `127.0.0.1:<high-port>`; PID stored in `$RUN_ROOT/qemu.pid`.

- [ ] **Step 1: Write failing QEMU boundary tests**

```python
def test_qemu_uses_kvm_overlay_and_loopback_only_user_networking(self):
    text = LAUNCHER.read_text()
    self.assertIn("-enable-kvm", text)
    self.assertIn("-cpu host", text)
    self.assertIn("-smp 2", text)
    self.assertIn("-m 4096", text)
    self.assertIn("overlay.qcow2", text)
    self.assertIn("hostfwd=tcp:127.0.0.1:", text)
    self.assertIn("-nic", text)
    self.assertIn("user,model=virtio-net-pci", text)
    for forbidden in ("tap,", "-netdev tap", "bridge", "macvtap"):
        self.assertNotIn(forbidden, text)
```

- [ ] **Step 2: Run test and verify RED**

```bash
python3 -m unittest -v tests.test_local_kvm_lab.LocalKvmLabTests.test_qemu_uses_kvm_overlay_and_loopback_only_user_networking
```

Expected: FAIL.

- [ ] **Step 3: Create overlay and enforce host resource floor**

Before launch, require at least 5 GiB MemAvailable and 30 GiB free space in the temp filesystem, then create a qcow2 overlay:

```bash
mem_kib=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
(( mem_kib >= 5 * 1024 * 1024 )) || refuse insufficient_host_memory
free_kib=$(df -Pk "${TMPDIR:-/tmp}" | awk 'NR==2 {print $4}')
(( free_kib >= 30 * 1024 * 1024 )) || refuse insufficient_host_disk

qemu-img create -q -f qcow2 -F qcow2 -b "$BASE_IMAGE" "$RUN_ROOT/overlay.qcow2" 24G
```

- [ ] **Step 4: Select a loopback-only SSH port and launch QEMU**

Choose a high port with Python loopback binding, then launch:

```bash
SSH_PORT=$(python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
)
readonly SSH_PORT

qemu-system-x86_64 \
  -enable-kvm -cpu host -smp 2 -m 4096 \
  -drive "file=$RUN_ROOT/overlay.qcow2,if=virtio,format=qcow2" \
  -drive "file=$RUN_ROOT/seed.img,if=virtio,format=raw,readonly=on" \
  -nic "user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:${SSH_PORT}-:22" \
  -display none -serial "file:$RUN_ROOT/serial.log" \
  -daemonize -pidfile "$RUN_ROOT/qemu.pid"
```

- [ ] **Step 5: Extend bounded cleanup to terminate only the recorded QEMU PID**

Verify the PID is numeric, belongs to the current user, and its `/proc/<pid>/cmdline` contains the exact run overlay path before sending TERM/KILL. Never use `pkill qemu`.

- [ ] **Step 6: Poll SSH and cloud-init readiness**

Use fixed SSH options only:

```bash
SSH=(ssh -i "$SSH_KEY" -p "$SSH_PORT" -o BatchMode=yes \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ConnectTimeout=3 mcf-lab@127.0.0.1)

for _ in $(seq 1 120); do
  if "${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1 && systemctl is-active --quiet docker.service'; then
    guest_ready=1
    break
  fi
  sleep 2
done
[[ ${guest_ready:-0} == 1 ]] || refuse guest_readiness_timeout
```

- [ ] **Step 7: Run focused tests and complete static suite**

```bash
python3 -m unittest -v tests.test_local_kvm_lab
PYTHON=python3 REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=0 scripts/test.sh
```

Expected: PASS without launching a VM on NODE-01 because these are static tests only.

- [ ] **Step 8: Commit Task 4**

```bash
git add scripts/run_f1_2c_kvm_lab.sh tests/test_local_kvm_lab.py
git commit -m "feat(f1.2c): boot isolated local KVM test guest"
```

---

### Task 5: Add a second explicit disposable identity to the existing privileged harness

**Files:**
- Modify: `scripts/test_node_network_services_vm.sh`
- Modify: `tests/test_node_network_services.py`
- Modify: `tests/test_local_kvm_lab.py`

**Interfaces:**
- Consumes GitHub path: `DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM=GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY` plus existing GitHub runner proofs.
- Consumes local KVM path: `DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM=MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY` plus KVM guest proofs.
- Produces: one shared privileged lifecycle after either complete identity gate succeeds.

- [ ] **Step 1: Write failing dual-gate tests**

Require that the GitHub token remains literally present and that a second KVM token is added. Require KVM checks for hostname prefix, `/etc/mcf-f1-2c-kvm-lab`, `MCF_F1_2C_KVM_LAB_V1`, Ubuntu 24.04, user `mcf-lab`, KVM/QEMU virtualization, `sudo -n true`, and explicit NODE-01 refusal.

Example:

```python
def test_disposable_harness_has_separate_github_and_local_kvm_gates(self):
    script = (ROOT / "scripts/test_node_network_services_vm.sh").read_text()
    self.assertIn("GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY", script)
    self.assertIn("MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY", script)
    self.assertIn("MCF_F1_2C_KVM_LAB_V1", script)
    self.assertIn("/etc/mcf-f1-2c-kvm-lab", script)
    self.assertIn("mcf-f1-2c-kvm-", script)
    self.assertIn("VERSION_ID=\"24.04\"", script)
    self.assertIn("systemd-detect-virt", script)
    self.assertIn("vmi3506102", script)
```

- [ ] **Step 2: Run focused tests and verify RED**

```bash
python3 -m unittest -v \
  tests.test_local_kvm_lab.LocalKvmLabTests.test_disposable_harness_has_separate_github_and_local_kvm_gates
```

Expected: FAIL because only GitHub-hosted identity exists.

- [ ] **Step 3: Refactor only the identity gate, not the privileged lifecycle**

At the top of `scripts/test_node_network_services_vm.sh`, keep the existing token and introduce:

```bash
readonly GITHUB_CONFIRMATION=GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY
readonly LOCAL_KVM_CONFIRMATION=MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY
```

Implement two functions:

```bash
verify_github_hosted_identity() {
  [[ ${GITHUB_ACTIONS:-} == true && ${RUNNER_ENVIRONMENT:-} == github-hosted ]] || return 1
  [[ ${ImageOS:-} == ubuntu24 && $(id -un) == runner ]] || return 1
  systemd-detect-virt --quiet --vm || return 1
}

verify_local_kvm_identity() {
  [[ $(id -un) == mcf-lab ]] || return 1
  [[ $(hostname --short) == mcf-f1-2c-kvm-* ]] || return 1
  [[ -f /etc/mcf-f1-2c-kvm-lab && ! -L /etc/mcf-f1-2c-kvm-lab ]] || return 1
  grep -Fxq MCF_F1_2C_KVM_LAB_V1 /etc/mcf-f1-2c-kvm-lab || return 1
  grep -Fxq 'VERSION_ID="24.04"' /etc/os-release || return 1
  case "$(systemd-detect-virt 2>/dev/null || true)" in kvm | qemu) ;; *) return 1 ;; esac
}
```

Select the identity by exact confirmation token and refuse otherwise. Retain the explicit `node-01 | vmi3506102` refusal and `sudo -n true` requirement before any cleanup or Docker mutation.

- [ ] **Step 4: Assert the privileged lifecycle body remains shared**

Update `tests/test_node_network_services.py` so it still requires the exact systemd unit path, Docker restart/reconcile, DNS/proxy/direct-egress checks, and rollback markers after the identity gate. Do not duplicate the lifecycle into separate GitHub/KVM scripts.

- [ ] **Step 5: Run focused and full tests**

```bash
python3 -m unittest -v tests.test_local_kvm_lab tests.test_node_network_services
PYTHON=python3 REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=0 scripts/test.sh
```

Expected: PASS.

- [ ] **Step 6: Commit Task 5**

```bash
git add scripts/test_node_network_services_vm.sh tests/test_node_network_services.py tests/test_local_kvm_lab.py
git commit -m "feat(f1.2c): authorize explicit local KVM disposable identity"
```

---

### Task 6: Transfer the exact candidate with Git bundle and execute the fixed guest lifecycle

**Files:**
- Modify: `scripts/run_f1_2c_kvm_lab.sh`
- Modify: `tests/test_local_kvm_lab.py`

**Interfaces:**
- Consumes: clean host checkout where `HEAD == CANDIDATE_SHA`, ready guest, ephemeral SSH key.
- Produces: guest checkout whose `git rev-parse HEAD` equals the requested SHA; then executes only `scripts/test_node_network_services_vm.sh` with the exact local-KVM confirmation token.

- [ ] **Step 1: Write failing candidate-transfer tests**

Require `git bundle create ... HEAD`, SCP to localhost guest only, clone from the bundle, exact SHA verification, and fixed harness invocation. Prohibit passing GitHub credentials or an arbitrary remote URL into the guest.

- [ ] **Step 2: Run focused test and verify RED**

```bash
python3 -m unittest -v tests.test_local_kvm_lab.LocalKvmLabTests.test_candidate_transfer_is_exact_bundle_and_fixed_guest_harness
```

Expected: FAIL.

- [ ] **Step 3: Create and transfer exact bundle**

```bash
git -C "$ROOT" bundle create "$RUN_ROOT/candidate.bundle" HEAD
scp -i "$SSH_KEY" -P "$SSH_PORT" -o BatchMode=yes \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$RUN_ROOT/candidate.bundle" mcf-lab@127.0.0.1:/tmp/candidate.bundle
```

- [ ] **Step 4: Reconstruct and verify candidate inside guest**

Use one fixed guest command string owned by the launcher, not caller input:

```bash
"${SSH[@]}" "set -Eeuo pipefail; \
  rm -rf -- /home/mcf-lab/cloud-infrastructure; \
  git clone /tmp/candidate.bundle /home/mcf-lab/cloud-infrastructure >/dev/null; \
  cd /home/mcf-lab/cloud-infrastructure; \
  test \"\$(git rev-parse HEAD)\" = '$CANDIDATE_SHA'; \
  test -z \"\$(git status --porcelain)\"; \
  DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM=MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY \
    scripts/test_node_network_services_vm.sh"
```

No operator-controlled second argument is interpolated as a command.

- [ ] **Step 5: Run static tests**

```bash
python3 -m unittest -v tests.test_local_kvm_lab
PYTHON=python3 REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=0 scripts/test.sh
```

Expected: PASS.

- [ ] **Step 6: Commit Task 6**

```bash
git add scripts/run_f1_2c_kvm_lab.sh tests/test_local_kvm_lab.py
git commit -m "feat(f1.2c): run exact candidate in disposable KVM guest"
```

---

### Task 7: Persist sanitized evidence and guarantee cleanup on PASS, FAIL, and signals

**Files:**
- Modify: `scripts/run_f1_2c_kvm_lab.sh`
- Modify: `tests/test_local_kvm_lab.py`

**Interfaces:**
- Produces persistent evidence under `${XDG_STATE_HOME:-$HOME/.local/state}/mcf-kvm-lab/evidence/<UTC>-<short-sha>/` containing `metadata.env`, `harness.log`, and `serial-tail.log`; ephemeral overlay/key/seed/PID are deleted.

- [ ] **Step 1: Write failing evidence/cleanup tests**

Require evidence fields: candidate SHA, image SHA, QEMU version, guest release, run ID, start/end UTC, exit code. Require no private-key copy, no full environment dump, no `set -x`, and bounded PID/path cleanup.

- [ ] **Step 2: Run tests and verify RED**

```bash
python3 -m unittest -v tests.test_local_kvm_lab.LocalKvmLabTests.test_evidence_is_non_secret_and_cleanup_is_bounded
```

Expected: FAIL.

- [ ] **Step 3: Capture sanitized guest output and metadata**

Pipe only the fixed harness stdout/stderr to `$EVIDENCE_DIR/harness.log`; capture at most the last 200 lines of QEMU serial log after shutdown. Write metadata with explicit fields, for example:

```text
candidate_sha=<40 hex>
image_sha256=6e40c07ae715f744f84af0bec76415cc1987dd115b4b8de437818561f01a3733
qemu_version=QEMU emulator version 8.2.2 ...
guest_release=24.04
run_id=<12 hex>
started_at=<UTC ISO-8601>
finished_at=<UTC ISO-8601>
harness_exit_code=0
```

Do not write SSH private-key material, Git config credentials, environment dumps, or cloud-init rendered user-data to durable evidence.

- [ ] **Step 4: Make PASS/FAIL explicit after cleanup**

The launcher saves the harness exit code, requests guest poweroff, performs validated QEMU cleanup, removes the run directory, then prints exactly one terminal status:

```bash
if (( harness_rc == 0 )); then
  printf 'KVM_LAB_PASS candidate=%s evidence=%s\n' "$CANDIDATE_SHA" "$EVIDENCE_DIR"
else
  printf 'KVM_LAB_FAIL candidate=%s rc=%s evidence=%s\n' "$CANDIDATE_SHA" "$harness_rc" "$EVIDENCE_DIR" >&2
  exit "$harness_rc"
fi
```

- [ ] **Step 5: Run static suite with shell validation**

```bash
python3 -m unittest -v tests.test_local_kvm_lab
bash -n scripts/run_f1_2c_kvm_lab.sh
bash -n scripts/test_node_network_services_vm.sh
PYTHON=python3 REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=0 scripts/test.sh
```

Expected: PASS.

- [ ] **Step 6: Commit Task 7**

```bash
git add scripts/run_f1_2c_kvm_lab.sh tests/test_local_kvm_lab.py
git commit -m "feat(f1.2c): persist KVM lab evidence and bounded cleanup"
```

---

### Task 8: Run fresh static verification on the self-hosted unprivileged runner

**Files:**
- Modify only if needed: validation workflow under `.github/workflows/` used for the existing unprivileged NODE-01 static probe.
- No NODE-01 privileged operation is authorized in this task.

**Interfaces:**
- Consumes: exact PR #9 head after Tasks 1-7.
- Produces: fresh log proving static tests pass with generic passwordless sudo unavailable and Docker socket unavailable.

- [ ] **Step 1: Point the existing static validation workflow at the exact new PR #9 head**

The workflow must use `[self-hosted, linux, x64, node-01, mcf-control]` and retain the negative boundaries:

```bash
if sudo -n true 2>/dev/null; then exit 1; fi
if [[ -S /var/run/docker.sock && -r /var/run/docker.sock && -w /var/run/docker.sock ]]; then exit 1; fi
```

- [ ] **Step 2: Run the complete static suite on that exact SHA**

```bash
PYTHON=python3 REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=0 scripts/test.sh
```

Expected: all Python tests and shell syntax checks PASS; no VM is started on NODE-01.

- [ ] **Step 3: Verify the workflow log and record exact run/job identifiers**

Evidence must show checkout of the expected PR #9 head, the negative privilege boundary, and the final test counts.

- [ ] **Step 4: Commit only workflow/evidence changes if required**

If the existing workflow already supports the exact head without code changes, do not create a gratuitous commit.

---

### Task 9: Execute the full KVM disposable integration on the operator workstation

**Files:**
- No code changes during the first acceptance run.
- Evidence is written by the launcher outside the repository.

**Interfaces:**
- Consumes: exact clean PR #9 candidate SHA after static verification.
- Produces: fresh disposable integration evidence sufficient to unlock canonical integration review if PASS.

- [ ] **Step 1: Prepare the local checkout without modifying it**

```bash
cd ~/Documentos/GitHub/cloud-infrastructure
git fetch origin
git switch fix/f1-2c-systemd-runtime-lock
git pull --ff-only
git status --short
git rev-parse HEAD
```

Expected: empty status and HEAD equal to the exact candidate to be tested.

- [ ] **Step 2: Run one command**

```bash
./scripts/run_f1_2c_kvm_lab.sh "$(git rev-parse HEAD)"
```

Expected host terminal status on success:

```text
KVM_LAB_PASS candidate=<exact-sha> evidence=<user-state-evidence-directory>
```

- [ ] **Step 3: Verify acceptance evidence**

The durable `harness.log` must contain the exact guest lifecycle PASS marker from `scripts/test_node_network_services_vm.sh`, including apply, idempotence, DNS, proxy, direct-egress denial, Docker restart reconciliation, and rollback cleanup. The guest must have exercised the exact `cloud-platform-network-services.service` unit under `ProtectSystem=strict`.

- [ ] **Step 4: Verify post-run host cleanup**

Confirm no QEMU process from the run remains and no `mcf-f1-2c-kvm.*` run directory remains under `${TMPDIR:-/tmp}`. The verified immutable base image may remain in the user cache by design.

- [ ] **Step 5: If FAIL, stop at evidence**

Do not retry blindly and do not apply the fix to NODE-01. Diagnose the disposable guest failure from `harness.log` and `serial-tail.log`, add a regression test, and return to the relevant TDD task.

---

### Task 10: Close the PR #9 validation gate without touching NODE-01

**Files:**
- Modify: `history/F1-2C-SYSTEMD-RUNTIME-LOCK-RECOVERY-2026-08-19.md`
- Modify only if consistent with canonical state rules: appropriate checkpoint/state file documenting fresh disposable evidence.

**Interfaces:**
- Consumes: exact PR #9 candidate SHA, fresh self-hosted static run evidence, fresh local KVM disposable run evidence.
- Produces: repository record that the runtime-lock fix has fresh full disposable evidence; PR remains subject to normal review/integration and NODE-01 recovery remains separately gated.

- [ ] **Step 1: Record exact evidence identifiers**

Write candidate SHA, local evidence directory basename, image SHA, static run/job IDs, KVM PASS marker, and the fact that NODE-01 was not mutated during disposable validation.

- [ ] **Step 2: Run state/document crosschecks**

```bash
PYTHON=python3 REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=0 scripts/test.sh
git diff --check
```

Expected: PASS.

- [ ] **Step 3: Commit validation evidence**

```bash
git add history/F1-2C-SYSTEMD-RUNTIME-LOCK-RECOVERY-2026-08-19.md state docs CHECKPOINT.md 2>/dev/null || true
git diff --cached --check
git commit -m "docs(f1.2c): record fresh KVM disposable integration evidence"
```

Stage only files actually changed and permitted by the state validators; do not force an unrelated state update.

- [ ] **Step 4: Re-run static verification if the evidence commit changes only non-executable material**

Use the approved evidence-inheritance classifier for the documentation-only delta. If it refuses, obtain fresh required evidence rather than overriding the gate.

- [ ] **Step 5: Stop before canonical merge or NODE-01 reapply unless their separate gates are satisfied**

PR #9 may become review-ready only after all preceding acceptance evidence is verified. Canonical integration and partial-state recovery/reapply on NODE-01 remain separate controlled operations.

---

## Self-Review Results

- **Spec coverage:** All specification sections are mapped: provenance (Tasks 1-2), isolation and host safety (Tasks 2 and 4), guest bootstrap (Task 3), candidate transfer (Task 6), dual identity gate and exact systemd lifecycle (Task 5), cleanup/evidence (Task 7), static runner proof (Task 8), real local KVM acceptance (Task 9), and repository evidence closure (Task 10).
- **Placeholder scan:** No `TBD`, `TODO`, “implement later”, or unspecified error-handling steps remain. The Ubuntu image URL and SHA-256 are pinned explicitly.
- **Interface consistency:** The launcher interface is consistently `scripts/run_f1_2c_kvm_lab.sh <candidate-sha>`; the local guest token is consistently `MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY`; the guest user is consistently `mcf-lab`; the marker is consistently `/etc/mcf-f1-2c-kvm-lab`; the guest hostname prefix is consistently `mcf-f1-2c-kvm-`.
- **Safety check:** No task authorizes host `sudo`, NODE-01 privileged VM execution, TAP/bridge networking, arbitrary guest commands, or reuse of the old disposable evidence for executable changes.
