#!/usr/bin/env bash
set -Eeuo pipefail

readonly GITHUB_CONFIRMATION=GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY
readonly LOCAL_KVM_CONFIRMATION=MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly BASE_SOURCE=$ROOT/platform/network/cloud-platform-network-enforcement
readonly BASE=/usr/local/libexec/cloud-platform-network-enforcement
readonly BASE_UNIT_SOURCE=$ROOT/platform/systemd/cloud-platform-network-enforcement.service
readonly BASE_UNIT=/etc/systemd/system/cloud-platform-network-enforcement.service
readonly SERVICE_SOURCE=$ROOT/platform/network/cloud-platform-network-services
readonly SERVICE=/usr/local/libexec/cloud-platform-network-services
readonly SERVICE_UNIT_SOURCE=$ROOT/platform/systemd/cloud-platform-network-services.service
readonly SERVICE_UNIT=/etc/systemd/system/cloud-platform-network-services.service
readonly SOURCE_CONFIG=$ROOT/platform/network/node-01
readonly CONFIG=/etc/cloud-platform/network-services
readonly SERVICE_MARKER=/etc/cloud-platform-network-services.managed
readonly SYSCTL=/etc/sysctl.d/90-cloud-platform-network-forwarding.conf
readonly BUSYBOX=busybox@sha256:7a3ebe5bfd1a4a19797d20b0c0bb39d44393e9a03fd852c0865b0f540d868df0

fail() { printf 'NODE_NETWORK_SERVICES_VM_FAIL reason=%s\n' "$1" >&2; exit 1; }

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

[[ $# -eq 0 ]] || fail unexpected_arguments
case ${DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM:-} in
  "$GITHUB_CONFIRMATION")
    verify_github_hosted_identity || fail invalid_github_hosted_identity
    ;;
  "$LOCAL_KVM_CONFIRMATION")
    verify_local_kvm_identity || fail invalid_local_kvm_identity
    ;;
  *) fail missing_exact_confirmation ;;
esac
case "$(hostname --short)" in node-01 | vmi3506102) fail real_dev_node ;; esac
sudo -n true >/dev/null 2>&1 || fail passwordless_sudo_unavailable
[[ -x $BASE_SOURCE && -f $BASE_UNIT_SOURCE && -x $SERVICE_SOURCE && -f $SERVICE_UNIT_SOURCE && -f $SOURCE_CONFIG/compose.yaml ]] ||
  fail source_missing
[[ -z $(sudo docker container ls --all --quiet) ]] || fail container_collision
[[ -z $(sudo docker volume ls --quiet) ]] || fail volume_collision
[[ -z $(sudo docker network ls --filter type=custom --quiet) ]] || fail network_collision
# GitHub-hosted images may contain rebuildable preloaded images. This destructive
# cleanup is permitted only after every disposable-runner gate above has passed.
sudo docker image prune --all --force >/dev/null
[[ -z $(sudo docker image ls --all --quiet) ]] || fail image_cleanup_failed

cleanup() {
  sudo docker rm --force cp-node-probe >/dev/null 2>&1 || true
  sudo docker image rm "$BUSYBOX" >/dev/null 2>&1 || true
  sudo systemctl disable --now cloud-platform-network-services.service >/dev/null 2>&1 || true
  if sudo test -x "$SERVICE" && sudo test -f "$SERVICE_MARKER"; then
    sudo "$SERVICE" rollback >/dev/null 2>&1 || true
  fi
  sudo unlink -- "$SERVICE_MARKER" "$SYSCTL" "$SERVICE" "$SERVICE_UNIT" >/dev/null 2>&1 || true
  sudo rm -f -- "$CONFIG/compose.yaml" \
    "$CONFIG/cp00000002/Corefile" "$CONFIG/cp00000002/records.hosts" \
    "$CONFIG/cp00000002/squid.conf" "$CONFIG/cp00000003/Corefile" \
    "$CONFIG/cp00000003/records.hosts" "$CONFIG/cp00000003/squid.conf" \
    >/dev/null 2>&1 || true
  sudo rmdir "$CONFIG/cp00000002" "$CONFIG/cp00000003" "$CONFIG" \
    /etc/cloud-platform >/dev/null 2>&1 || true
  sudo systemctl disable --now cloud-platform-network-enforcement.service >/dev/null 2>&1 || true
  if sudo test -x "$BASE"; then sudo "$BASE" rollback >/dev/null 2>&1 || true; fi
  sudo unlink -- "$BASE" "$BASE_UNIT" >/dev/null 2>&1 || true
  sudo systemctl daemon-reload >/dev/null 2>&1 || true
}
trap cleanup EXIT

sudo install -d -o root -g root -m 0755 /usr/local/libexec
sudo install -o root -g root -m 0755 "$BASE_SOURCE" "$BASE"
sudo "$BASE" apply | grep -q 'changed=1' || fail base_apply_failed
sudo install -o root -g root -m 0644 "$BASE_UNIT_SOURCE" "$BASE_UNIT"
sudo systemctl daemon-reload
sudo systemctl enable --now cloud-platform-network-enforcement.service
sudo systemctl is-active --quiet cloud-platform-network-enforcement.service || fail base_unit_inactive

sudo install -d -o root -g root -m 0755 "$CONFIG/cp00000002" "$CONFIG/cp00000003"
sudo install -o root -g root -m 0755 "$SERVICE_SOURCE" "$SERVICE"
sudo install -o root -g root -m 0644 "$SOURCE_CONFIG/compose.yaml" "$CONFIG/compose.yaml"
for scope in cp00000002 cp00000003; do
  for file in Corefile records.hosts squid.conf; do
    sudo install -o root -g root -m 0644 "$SOURCE_CONFIG/$scope/$file" "$CONFIG/$scope/$file"
  done
done
sudo install -o root -g root -m 0644 \
  "$ROOT/platform/sysctl/90-cloud-platform-network-forwarding.conf" "$SYSCTL"
printf '%s\n' SLICE-002C-NODE-01-SERVICES-V1 | sudo tee "$SERVICE_MARKER" >/dev/null
sudo chown root:root "$SERVICE_MARKER"
sudo chmod 0600 "$SERVICE_MARKER"
sudo install -o root -g root -m 0644 "$SERVICE_UNIT_SOURCE" "$SERVICE_UNIT"
sudo systemctl daemon-reload
if ! sudo systemctl enable --now cloud-platform-network-services.service; then
  sudo systemctl status cloud-platform-network-services.service --no-pager --full >&2 || true
  sudo journalctl -u cloud-platform-network-services.service -n 120 --no-pager >&2 || true
  fail systemd_service_start_failed
fi
sudo systemctl is-active --quiet cloud-platform-network-services.service || fail systemd_service_inactive
sudo journalctl -u cloud-platform-network-services.service -n 120 --no-pager | \
  grep -q 'NETWORK_SERVICES_APPLY=PASS changed=1' || fail systemd_first_apply_evidence_missing

sudo "$SERVICE" apply | grep -q 'changed=0' || fail idempotence_failed
sudo "$SERVICE" check | grep -q 'NETWORK_SERVICES_CHECK=PASS' || fail check_failed

sudo docker pull "$BUSYBOX" >/dev/null
probe() {
  timeout --kill-after=2s 12s sudo docker run --rm --name cp-node-probe \
    --network cloud-scope-cp00000002 --read-only --cap-drop ALL \
    --security-opt no-new-privileges --pids-limit 32 --memory 32m --cpus 0.25 \
    "$BUSYBOX" "$@"
}
probe nslookup api.github.com 10.240.2.2 >/dev/null || fail scoped_dns_failed
if probe wget -T 4 -qO- https://api.github.com >/dev/null 2>&1; then
  fail direct_egress_allowed
fi
if ! probe sh -c \
  'http_proxy=http://10.240.2.3:3128 wget -T 8 -qO- http://security.ubuntu.com/ubuntu/ >/dev/null'; then
  sudo docker logs --tail 80 cp-proxy-dev >&2 || true
  fail development_proxy_failed
fi
sudo docker image rm "$BUSYBOX" >/dev/null

sudo systemctl restart docker.service
sudo systemctl is-active --quiet cloud-platform-network-enforcement.service || fail base_inactive_after_docker_restart
sudo systemctl is-active --quiet cloud-platform-network-services.service || fail services_inactive_after_docker_restart
sudo "$SERVICE" check >/dev/null || fail post_restart_check_failed
sudo journalctl -u cloud-platform-network-services.service -n 160 --no-pager | \
  grep -q 'NETWORK_SERVICES_APPLY=PASS changed=1' || fail post_restart_reconcile_evidence_missing

sudo systemctl disable --now cloud-platform-network-services.service
sudo "$SERVICE" rollback | grep -q 'NETWORK_SERVICES_ROLLBACK=PASS' || fail rollback_failed
for managed_file in "$SERVICE_MARKER" "$SYSCTL" "$SERVICE" "$SERVICE_UNIT"; do
  sudo unlink -- "$managed_file"
done
sudo rm -f -- "$CONFIG/compose.yaml" \
  "$CONFIG/cp00000002/Corefile" "$CONFIG/cp00000002/records.hosts" \
  "$CONFIG/cp00000002/squid.conf" "$CONFIG/cp00000003/Corefile" \
  "$CONFIG/cp00000003/records.hosts" "$CONFIG/cp00000003/squid.conf"
sudo rmdir "$CONFIG/cp00000002" "$CONFIG/cp00000003" "$CONFIG" /etc/cloud-platform
sudo systemctl disable --now cloud-platform-network-enforcement.service
sudo "$BASE" rollback >/dev/null
sudo unlink -- "$BASE" "$BASE_UNIT"
sudo systemctl daemon-reload
[[ -z $(sudo docker container ls --all --quiet) ]] || fail containers_remained
[[ -z $(sudo docker image ls --all --quiet) ]] || fail images_remained
[[ -z $(sudo docker network ls --filter type=custom --quiet) ]] || fail networks_remained
[[ $(sysctl -n net.ipv4.ip_forward) == 0 ]] || fail forwarding_remained
trap - EXIT
printf '%s\n' \
  'NODE_NETWORK_SERVICES_VM_PASS apply=systemd idempotence=0 dns=pass proxy=pass direct=denied restart=systemd rollback=clean scope=disposable_only'
