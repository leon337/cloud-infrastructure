#!/usr/bin/env bash
set -Eeuo pipefail

readonly EXPECTED_CONFIRMATION=GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY
readonly SCRIPT_SOURCE=/workspace/cloud-infrastructure/platform/network/cloud-platform-network-enforcement
readonly UNIT_SOURCE=/workspace/cloud-infrastructure/platform/systemd/cloud-platform-network-enforcement.service
readonly DROPIN_SOURCE=/workspace/cloud-infrastructure/platform/systemd/docker.service.network-enforcement.conf
readonly SCRIPT_DESTINATION=/usr/local/libexec/cloud-platform-network-enforcement
readonly UNIT_DESTINATION=/etc/systemd/system/cloud-platform-network-enforcement.service
readonly DROPIN_DESTINATION=/etc/systemd/system/docker.service.d/20-cloud-platform-network-enforcement.conf
readonly MARKER=/etc/cloud-platform-network-enforcement.managed

fail() {
  printf 'NETWORK_ENFORCEMENT_VM_TEST_FAIL reason=%s\n' "$1" >&2
  exit 1
}

[[ $# -eq 0 ]] || fail unexpected_arguments
[[ ${DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM:-} == "$EXPECTED_CONFIRMATION" ]] ||
  fail missing_exact_confirmation
[[ ${GITHUB_ACTIONS:-} == true && ${RUNNER_ENVIRONMENT:-} == github-hosted ]] ||
  fail not_github_hosted
[[ ${ImageOS:-} == ubuntu24 && $(id -un) == runner ]] || fail unexpected_runner
case "$(hostname --short)" in node-01 | vmi3506102) fail real_dev_node ;; esac
systemd-detect-virt --quiet --vm || fail not_disposable_vm
sudo -n true >/dev/null 2>&1 || fail passwordless_sudo_unavailable
[[ -x $SCRIPT_SOURCE && -f $UNIT_SOURCE && -f $DROPIN_SOURCE ]] || fail payload_missing
[[ ! -e $SCRIPT_DESTINATION && ! -L $SCRIPT_DESTINATION ]] || fail script_collision
[[ ! -e $UNIT_DESTINATION && ! -L $UNIT_DESTINATION ]] || fail unit_collision
[[ ! -e $DROPIN_DESTINATION && ! -L $DROPIN_DESTINATION ]] || fail dropin_collision
[[ ! -e $MARKER && ! -L $MARKER ]] || fail marker_collision
sudo systemctl is-active --quiet docker.service || fail docker_inactive

cleanup() {
  sudo ip link delete cpdeadbeef >/dev/null 2>&1 || true
  if sudo test -x "$SCRIPT_DESTINATION"; then
    sudo systemctl disable --now cloud-platform-network-enforcement.service \
      >/dev/null 2>&1 || true
    if sudo test -f "$MARKER"; then
      sudo "$SCRIPT_DESTINATION" rollback >/dev/null 2>&1 || true
    fi
  fi
  sudo unlink -- "$UNIT_DESTINATION" >/dev/null 2>&1 || true
  sudo unlink -- "$DROPIN_DESTINATION" >/dev/null 2>&1 || true
  sudo unlink -- "$SCRIPT_DESTINATION" >/dev/null 2>&1 || true
  sudo systemctl daemon-reload >/dev/null 2>&1 || true
}
trap cleanup EXIT

sudo install -d -o root -g root -m 0755 /usr/local/libexec
sudo install -o root -g root -m 0755 "$SCRIPT_SOURCE" "$SCRIPT_DESTINATION"
sudo install -o root -g root -m 0644 "$UNIT_SOURCE" "$UNIT_DESTINATION"
sudo install -o root -g root -m 0644 "$DROPIN_SOURCE" "$DROPIN_DESTINATION"

first_output=$(sudo "$SCRIPT_DESTINATION" apply)
grep -q 'NETWORK_ENFORCEMENT_APPLY=PASS changed=1' <<<"$first_output" ||
  fail first_apply_not_changed
sudo systemctl daemon-reload
sudo systemctl enable --now cloud-platform-network-enforcement.service
second_output=$(sudo "$SCRIPT_DESTINATION" apply)
grep -q 'NETWORK_ENFORCEMENT_APPLY=PASS changed=0' <<<"$second_output" ||
  fail second_apply_not_idempotent
sudo "$SCRIPT_DESTINATION" check | grep -q 'NETWORK_ENFORCEMENT_CHECK=PASS' ||
  fail initial_check_failed

for tool in iptables ip6tables; do
  sudo "$tool" -C INPUT -i 'cp+' -j CLOUD-PLATFORM-IN || fail input_jump_missing
  sudo "$tool" -C DOCKER-USER -i 'cp+' -j CLOUD-PLATFORM-FWD ||
    fail ingress_forward_jump_missing
  sudo "$tool" -C DOCKER-USER -o 'cp+' -j CLOUD-PLATFORM-FWD ||
    fail egress_forward_jump_missing
done

sudo ip link add cpdeadbeef type dummy
if refusal_output=$(sudo "$SCRIPT_DESTINATION" rollback 2>&1); then
  fail rollback_accepted_live_interface
fi
grep -q 'managed_interface_still_present' <<<"$refusal_output" ||
  fail rollback_refusal_reason_missing
sudo ip link delete cpdeadbeef
sudo "$SCRIPT_DESTINATION" check >/dev/null || fail refusal_mutated_rules

sudo systemctl restart docker.service
sudo systemctl is-active --quiet cloud-platform-network-enforcement.service ||
  fail service_not_restarted_with_docker
sudo "$SCRIPT_DESTINATION" check >/dev/null || fail post_restart_check_failed

sudo systemctl disable --now cloud-platform-network-enforcement.service
sudo "$SCRIPT_DESTINATION" rollback |
  grep -q 'NETWORK_ENFORCEMENT_ROLLBACK=PASS' || fail rollback_failed
sudo test ! -e "$MARKER" || fail marker_survived_rollback
for tool in iptables ip6tables; do
  if sudo "$tool" -nL CLOUD-PLATFORM-IN >/dev/null 2>&1; then
    fail input_chain_survived_rollback
  fi
  if sudo "$tool" -nL CLOUD-PLATFORM-FWD >/dev/null 2>&1; then
    fail forward_chain_survived_rollback
  fi
done

sudo unlink -- "$UNIT_DESTINATION"
sudo unlink -- "$DROPIN_DESTINATION"
sudo unlink -- "$SCRIPT_DESTINATION"
sudo systemctl daemon-reload
trap - EXIT
printf '%s\n' \
  'NETWORK_ENFORCEMENT_VM_TEST_PASS apply=changed_1 idempotence=changed_0 ipv4=pass ipv6=pass restart=pass refusal=pass rollback=clean'
