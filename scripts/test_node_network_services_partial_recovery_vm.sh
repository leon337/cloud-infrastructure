#!/usr/bin/env bash
set -Eeuo pipefail

readonly CONFIRMATION=MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY
readonly RECOVERY_CONFIRMATION=F1_2C_RECOVERY_DISPOSABLE_KVM_ONLY
readonly HISTORICAL_PARTIAL_COMMIT=c9f909945b544d22dbabc619252456f7190f7ae9
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly RECOVERY=$ROOT/automation/mission-001/operations/recover-network-services-partial
readonly BASE_SOURCE=$ROOT/platform/network/cloud-platform-network-enforcement
readonly BASE=/usr/local/libexec/cloud-platform-network-enforcement
readonly BASE_UNIT_SOURCE=$ROOT/platform/systemd/cloud-platform-network-enforcement.service
readonly BASE_UNIT=/etc/systemd/system/cloud-platform-network-enforcement.service
readonly BASE_DROPIN_SOURCE=$ROOT/platform/systemd/docker.service.network-enforcement.conf
readonly BASE_DROPIN=/etc/systemd/system/docker.service.d/20-cloud-platform-network-enforcement.conf
readonly SERVICE=/usr/local/libexec/cloud-platform-network-services
readonly SERVICE_UNIT=/etc/systemd/system/cloud-platform-network-services.service
readonly SERVICE_MARKER=/etc/cloud-platform-network-services.managed
readonly SERVICE_ROOT=/etc/cloud-platform/network-services
readonly SYSCTL=/etc/sysctl.d/90-cloud-platform-network-forwarding.conf
readonly LEGACY_LOCK=/run/lock/cloud-platform-network-services.lock
readonly RECOVERY_STATE=/var/lib/cloud-platform-f1-2c-partial-recovery
readonly BACKUP=/usr/local/sbin/cloud-infrastructure-config-backup
readonly OLD_HELPER_SHA=06d0f016809a2e8d9cf0be5a258766563cc686fe40b21ec3578a99c731421060
readonly OLD_UNIT_SHA=dfe10b0e0046242695fe5ba03215f49aa938cf94b733bba3b1a2ba9cfad7e6d1

fail() { printf 'NODE_NETWORK_SERVICES_PARTIAL_RECOVERY_VM_FAIL reason=%s\n' "$1" >&2; exit 1; }
sha_of() { sha256sum "$1" | awk '{print $1}'; }

[[ $# -eq 0 ]] || fail unexpected_arguments
[[ ${DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM:-} == "$CONFIRMATION" ]] || fail missing_exact_confirmation
[[ $(id -un) == mcf-lab ]] || fail wrong_user
[[ $(hostname --short) == mcf-f1-2c-kvm-* ]] || fail wrong_host
[[ -f /etc/mcf-f1-2c-kvm-lab && ! -L /etc/mcf-f1-2c-kvm-lab ]] || fail kvm_marker_missing
sudo -n grep -Fxq MCF_F1_2C_KVM_LAB_V1 /etc/mcf-f1-2c-kvm-lab || fail kvm_marker_drift
case "$(systemd-detect-virt 2>/dev/null || true)" in kvm | qemu) ;; *) fail not_kvm ;; esac
sudo -n true >/dev/null 2>&1 || fail passwordless_sudo_unavailable
[[ -x $RECOVERY && -x $BASE_SOURCE && -f $BASE_UNIT_SOURCE && -f $BASE_DROPIN_SOURCE ]] || fail source_missing
candidate_sha=$(git -C "$ROOT" rev-parse HEAD)
[[ $candidate_sha =~ ^[0-9a-f]{40}$ ]] || fail candidate_sha_invalid
git -C "$ROOT" merge-base --is-ancestor "$HISTORICAL_PARTIAL_COMMIT" "$candidate_sha" || fail historical_commit_not_reachable

old_root=$(mktemp -d /tmp/f1-2c-old-partial.XXXXXX)
cleanup() {
  sudo systemctl stop cloud-platform-network-services.service >/dev/null 2>&1 || true
  if sudo test -x "$SERVICE" && sudo "$SERVICE" check >/dev/null 2>&1; then
    sudo "$SERVICE" rollback >/dev/null 2>&1 || true
  fi
  sudo systemctl disable cloud-platform-network-services.service >/dev/null 2>&1 || true
  sudo rm -rf --one-file-system "$RECOVERY_STATE" >/dev/null 2>&1 || true
  sudo rm -f -- "$SERVICE_MARKER" "$SYSCTL" "$SERVICE" "$SERVICE_UNIT" "$LEGACY_LOCK" >/dev/null 2>&1 || true
  sudo rm -f -- "$SERVICE_ROOT/compose.yaml" \
    "$SERVICE_ROOT/cp00000002/Corefile" "$SERVICE_ROOT/cp00000002/records.hosts" \
    "$SERVICE_ROOT/cp00000002/squid.conf" "$SERVICE_ROOT/cp00000003/Corefile" \
    "$SERVICE_ROOT/cp00000003/records.hosts" "$SERVICE_ROOT/cp00000003/squid.conf" \
    >/dev/null 2>&1 || true
  sudo rmdir "$SERVICE_ROOT/cp00000002" "$SERVICE_ROOT/cp00000003" "$SERVICE_ROOT" /etc/cloud-platform >/dev/null 2>&1 || true
  sudo rm -f -- /etc/cloud-platform-foundation.managed /etc/cloud-platform-docker-runtime.managed >/dev/null 2>&1 || true
  sudo rm -f -- "$BACKUP" /var/tmp/f1-2c-recovery-backup.log >/dev/null 2>&1 || true
  sudo systemctl disable --now cloud-platform-network-enforcement.service >/dev/null 2>&1 || true
  if sudo test -x "$BASE"; then sudo "$BASE" rollback >/dev/null 2>&1 || true; fi
  sudo rm -f -- "$BASE_DROPIN" "$BASE_UNIT" "$BASE" /etc/cloud-platform-network-enforcement.managed >/dev/null 2>&1 || true
  sudo systemctl daemon-reload >/dev/null 2>&1 || true
  rm -rf --one-file-system "$old_root"
}
trap cleanup EXIT

[[ -z $(sudo docker container ls --all --quiet) ]] || fail container_collision
[[ -z $(sudo docker volume ls --quiet) ]] || fail volume_collision
[[ -z $(sudo docker network ls --filter type=custom --quiet) ]] || fail network_collision
sudo docker image prune --all --force >/dev/null
[[ -z $(sudo docker image ls --all --quiet) ]] || fail image_cleanup_failed
# Mirror the NODE-01 F1.2b Docker socket boundary in the disposable guest.
sudo chown root:root /var/run/docker.sock
sudo chmod 0600 /var/run/docker.sock
[[ $(sudo stat -c '%U:%G:%a' /var/run/docker.sock) == root:root:600 ]] || fail docker_socket_boundary_failed

# Previous layers and base enforcement are deliberately recreated before the
# historical partial network-services start.
printf '%s' 'managed_by=cloud-infrastructure
slice=SLICE-001
schema=1
environment=dev
node=node-01' | sudo tee /etc/cloud-platform-foundation.managed >/dev/null
printf '%s' 'managed_by=cloud-infrastructure
slice=SLICE-002B
schema=1
environment=dev
node=node-01
runtime=docker-ce
docker_ce=5:29.7.2-1~ubuntu.24.04~noble
containerd_io=2.3.3-1~ubuntu.24.04~noble' | sudo tee /etc/cloud-platform-docker-runtime.managed >/dev/null
sudo chown root:root /etc/cloud-platform-foundation.managed /etc/cloud-platform-docker-runtime.managed
sudo chmod 0600 /etc/cloud-platform-foundation.managed /etc/cloud-platform-docker-runtime.managed
sudo install -d -o root -g root -m 0755 /usr/local/libexec /etc/systemd/system/docker.service.d
sudo install -o root -g root -m 0755 "$BASE_SOURCE" "$BASE"
sudo "$BASE" apply | grep -q 'changed=1' || fail base_apply_failed
sudo install -o root -g root -m 0644 "$BASE_UNIT_SOURCE" "$BASE_UNIT"
sudo install -o root -g root -m 0644 "$BASE_DROPIN_SOURCE" "$BASE_DROPIN"
sudo systemctl daemon-reload
sudo systemctl enable --now cloud-platform-network-enforcement.service >/dev/null
sudo "$BASE" check >/dev/null || fail base_check_failed

# Historical helper/unit are sourced from the exact commit that matches the
# current NODE-01 installed SHA-256 inventory.
git -C "$ROOT" show "$HISTORICAL_PARTIAL_COMMIT:platform/network/cloud-platform-network-services" >"$old_root/helper"
git -C "$ROOT" show "$HISTORICAL_PARTIAL_COMMIT:platform/systemd/cloud-platform-network-services.service" >"$old_root/unit"
[[ $(sha_of "$old_root/helper") == "$OLD_HELPER_SHA" ]] || fail historical_helper_hash_mismatch
[[ $(sha_of "$old_root/unit") == "$OLD_UNIT_SHA" ]] || fail historical_unit_hash_mismatch
sudo install -o root -g root -m 0755 "$old_root/helper" "$SERVICE"
sudo install -o root -g root -m 0644 "$old_root/unit" "$SERVICE_UNIT"
sudo install -o root -g root -m 0644 "$ROOT/platform/sysctl/90-cloud-platform-network-forwarding.conf" "$SYSCTL"
printf '%s\n' SLICE-002C-NODE-01-SERVICES-V1 | sudo tee "$SERVICE_MARKER" >/dev/null
sudo chown root:root "$SERVICE_MARKER"
sudo chmod 0600 "$SERVICE_MARKER"
sudo install -o root -g root -m 0600 /dev/null "$LEGACY_LOCK"
# Remove only the private runtime residue left by the preceding normal-lifecycle
# test in this same disposable guest before reproducing the NODE-01 partial state.
sudo rm -f -- /run/cloud-platform-network-services/lock
sudo rmdir /run/cloud-platform-network-services 2>/dev/null || true
# No service config tree is installed: this mirrors the live partial state.
sudo test ! -e "$SERVICE_ROOT" || fail partial_config_root_exists
sudo test ! -e /run/cloud-platform-network-services || fail private_runtime_preexists
sudo systemctl daemon-reload
sudo systemctl enable cloud-platform-network-services.service >/dev/null
set +e
sudo systemctl start cloud-platform-network-services.service
old_rc=$?
set -e
[[ $old_rc -ne 0 ]] || fail historical_unit_unexpectedly_started
sudo systemctl is-failed --quiet cloud-platform-network-services.service || fail historical_unit_not_failed
sudo journalctl -u cloud-platform-network-services.service -n 80 --no-pager |
  grep -F '/run/lock/cloud-platform-network-services.lock: Read-only file system' >/dev/null ||
  fail historical_lock_failure_not_reproduced

# Test-only backup command proves the recovery actually invokes the checkpoint backup gate.
cat >"$old_root/backup" <<'BACKUP'
#!/usr/bin/env bash
set -Eeuo pipefail
printf 'KVM_BACKUP_CALLED\n' >>/var/tmp/f1-2c-recovery-backup.log
BACKUP
sudo install -o root -g root -m 0750 "$old_root/backup" "$BACKUP"
sudo rm -f /var/tmp/f1-2c-recovery-backup.log

RECOVERY_ENV=(
  env
  F1_2C_RECOVERY_TEST_CONFIRM="$RECOVERY_CONFIRMATION"
  F1_2C_RECOVERY_CANDIDATE_SHA="$candidate_sha"
)

sudo "${RECOVERY_ENV[@]}" "$RECOVERY" precheck | grep -F 'RECOVERY_PRECHECK=PASS' >/dev/null || fail recovery_precheck_failed
sudo "${RECOVERY_ENV[@]}" "$RECOVERY" apply | grep -F 'RECOVERY_APPLY=PASS changed=1' >/dev/null || fail recovery_apply_failed
sudo test -s /var/tmp/f1-2c-recovery-backup.log || fail recovery_backup_not_called
sudo "${RECOVERY_ENV[@]}" "$RECOVERY" check | grep -F 'RECOVERY_CHECK=PASS' >/dev/null || fail recovery_check_failed
sudo "${RECOVERY_ENV[@]}" "$RECOVERY" apply | grep -F 'RECOVERY_APPLY=PASS changed=0' >/dev/null || fail recovery_idempotence_failed
sudo systemctl is-active --quiet cloud-platform-network-services.service || fail recovered_service_inactive
sudo "$SERVICE" check >/dev/null || fail recovered_helper_check_failed
[[ $(sysctl -n net.ipv4.ip_forward) == 1 ]] || fail recovered_ipv4_forwarding_missing
[[ $(sysctl -n net.ipv6.conf.all.forwarding) == 0 ]] || fail recovered_ipv6_forwarding_drift

sudo "${RECOVERY_ENV[@]}" "$RECOVERY" rollback | grep -F 'RECOVERY_ROLLBACK=PASS' >/dev/null || fail recovery_rollback_failed
[[ $(sudo sha256sum "$SERVICE" | awk '{print $1}') == "$OLD_HELPER_SHA" ]] || fail old_helper_not_restored
[[ $(sudo sha256sum "$SERVICE_UNIT" | awk '{print $1}') == "$OLD_UNIT_SHA" ]] || fail old_unit_not_restored
sudo test ! -e "$SERVICE_ROOT" || fail config_root_remained_after_rollback
[[ -z $(sudo docker container ls --all --quiet) ]] || fail containers_remained_after_rollback
[[ -z $(sudo docker image ls --all --quiet) ]] || fail images_remained_after_rollback
[[ -z $(sudo docker network ls --filter type=custom --quiet) ]] || fail networks_remained_after_rollback
[[ $(sysctl -n net.ipv4.ip_forward) == 0 ]] || fail forwarding_remained_after_rollback
sudo systemctl is-enabled --quiet cloud-platform-network-services.service || fail service_enablement_not_preserved
sudo grep -Fxq ROLLED_BACK_SAFE_PARTIAL "$RECOVERY_STATE/state" || fail rollback_state_marker_missing

trap - EXIT
cleanup
printf '%s\n' 'NODE_NETWORK_SERVICES_PARTIAL_RECOVERY_VM_PASS historical_failure=pass precheck=pass apply=pass check=pass idempotence=pass rollback=pass cleanup=pass'
