#!/usr/bin/env bash
set -Eeuo pipefail

readonly CONFIRMATION=GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly ENFORCEMENT_SOURCE=$ROOT/platform/network/cloud-platform-network-enforcement
readonly ENFORCEMENT_DESTINATION=/usr/local/libexec/cloud-platform-network-enforcement
readonly RECONCILER=$ROOT/scripts/reconcile_network_scopes.py
readonly POLICY=$ROOT/platform/network/f1-2c-policy.disposable.yaml
readonly SERVICES_HARNESS=$ROOT/scripts/test_network_services_vm.sh
readonly MARKER=/etc/cloud-platform-network-enforcement.managed

fail() {
  printf 'NETWORK_SERVICES_STANDALONE_VM_TEST_FAIL reason=%s\n' "$1" >&2
  exit 1
}

[[ $# -eq 0 ]] || fail unexpected_arguments
[[ ${DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM:-} == "$CONFIRMATION" ]] ||
  fail missing_exact_confirmation
[[ ${GITHUB_ACTIONS:-} == true && ${RUNNER_ENVIRONMENT:-} == github-hosted ]] ||
  fail not_github_hosted
[[ ${ImageOS:-} == ubuntu24 && $(id -un) == runner ]] || fail unexpected_runner
case "$(hostname --short)" in node-01 | vmi3506102) fail real_dev_node ;; esac
systemd-detect-virt --quiet --vm || fail not_disposable_vm
sudo -n true >/dev/null 2>&1 || fail passwordless_sudo_unavailable
[[ -x $ENFORCEMENT_SOURCE && -x $RECONCILER && -x $SERVICES_HARNESS ]] ||
  fail payload_missing
sudo systemctl is-active --quiet docker.service || fail docker_inactive
[[ ! -e $ENFORCEMENT_DESTINATION && ! -L $ENFORCEMENT_DESTINATION ]] ||
  fail enforcement_collision
[[ ! -e $MARKER && ! -L $MARKER ]] || fail marker_collision

cleanup() {
  local network
  for network in cloud-scope-cp00000001 cloud-scope-cp00000002 cloud-scope-cp00000003; do
    sudo docker network rm "$network" >/dev/null 2>&1 || true
  done
  if sudo test -x "$ENFORCEMENT_DESTINATION"; then
    sudo "$ENFORCEMENT_DESTINATION" rollback >/dev/null 2>&1 || true
  fi
  sudo unlink -- "$ENFORCEMENT_DESTINATION" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sudo install -d -o root -g root -m 0755 /usr/local/libexec
sudo install -o root -g root -m 0755 "$ENFORCEMENT_SOURCE" "$ENFORCEMENT_DESTINATION"
sudo "$ENFORCEMENT_DESTINATION" apply |
  grep -q 'NETWORK_ENFORCEMENT_APPLY=PASS' || fail enforcement_apply_failed

export F1_2C_NETWORK_SCOPE_CONFIRM=$CONFIRMATION
sudo --preserve-env=F1_2C_NETWORK_SCOPE_CONFIRM,GITHUB_ACTIONS,RUNNER_ENVIRONMENT,ImageOS \
  "$RECONCILER" apply "$POLICY" |
  grep -q 'NETWORK_SCOPES_APPLY=PASS changed=3' || fail scope_apply_failed

NETWORK_SERVICES_ROOT=$ROOT "$SERVICES_HARNESS"

sudo --preserve-env=F1_2C_NETWORK_SCOPE_CONFIRM,GITHUB_ACTIONS,RUNNER_ENVIRONMENT,ImageOS \
  "$RECONCILER" rollback "$POLICY" |
  grep -q 'NETWORK_SCOPES_ROLLBACK=PASS changed=3' || fail scope_rollback_failed
sudo "$ENFORCEMENT_DESTINATION" rollback |
  grep -q 'NETWORK_ENFORCEMENT_ROLLBACK=PASS' || fail enforcement_rollback_failed
sudo unlink -- "$ENFORCEMENT_DESTINATION"
trap - EXIT

printf '%s\n' \
  'NETWORK_SERVICES_STANDALONE_VM_TEST_PASS isolation=pass services=pass rollback=clean scope=disposable_only'
