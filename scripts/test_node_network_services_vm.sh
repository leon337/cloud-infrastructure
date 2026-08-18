#!/usr/bin/env bash
set -Eeuo pipefail

readonly CONFIRMATION=GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly BASE_SOURCE=$ROOT/platform/network/cloud-platform-network-enforcement
readonly BASE=/usr/local/libexec/cloud-platform-network-enforcement
readonly SERVICE_SOURCE=$ROOT/platform/network/cloud-platform-network-services
readonly SERVICE=/usr/local/libexec/cloud-platform-network-services
readonly SOURCE_CONFIG=$ROOT/platform/network/node-01
readonly CONFIG=/etc/cloud-platform/network-services
readonly SERVICE_MARKER=/etc/cloud-platform-network-services.managed
readonly SYSCTL=/etc/sysctl.d/90-cloud-platform-network-forwarding.conf
readonly BUSYBOX=busybox@sha256:7a3ebe5bfd1a4a19797d20b0c0bb39d44393e9a03fd852c0865b0f540d868df0

fail() { printf 'NODE_NETWORK_SERVICES_VM_FAIL reason=%s\n' "$1" >&2; exit 1; }

[[ $# -eq 0 ]] || fail unexpected_arguments
[[ ${DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM:-} == "$CONFIRMATION" ]] ||
  fail missing_exact_confirmation
[[ ${GITHUB_ACTIONS:-} == true && ${RUNNER_ENVIRONMENT:-} == github-hosted ]] ||
  fail not_github_hosted
[[ ${ImageOS:-} == ubuntu24 && $(id -un) == runner ]] || fail unexpected_runner
case "$(hostname --short)" in node-01 | vmi3506102) fail real_dev_node ;; esac
systemd-detect-virt --quiet --vm || fail not_disposable_vm
sudo -n true >/dev/null 2>&1 || fail passwordless_sudo_unavailable
[[ -x $BASE_SOURCE && -x $SERVICE_SOURCE && -f $SOURCE_CONFIG/compose.yaml ]] ||
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
  if sudo test -x "$SERVICE" && sudo test -f "$SERVICE_MARKER"; then
    sudo "$SERVICE" rollback >/dev/null 2>&1 || true
  fi
  sudo unlink -- "$SERVICE_MARKER" "$SYSCTL" "$SERVICE" >/dev/null 2>&1 || true
  sudo rm -f -- "$CONFIG/compose.yaml" \
    "$CONFIG/cp00000002/Corefile" "$CONFIG/cp00000002/records.hosts" \
    "$CONFIG/cp00000002/squid.conf" "$CONFIG/cp00000003/Corefile" \
    "$CONFIG/cp00000003/records.hosts" "$CONFIG/cp00000003/squid.conf" \
    >/dev/null 2>&1 || true
  sudo rmdir "$CONFIG/cp00000002" "$CONFIG/cp00000003" "$CONFIG" \
    /etc/cloud-platform >/dev/null 2>&1 || true
  if sudo test -x "$BASE"; then sudo "$BASE" rollback >/dev/null 2>&1 || true; fi
  sudo unlink -- "$BASE" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sudo install -d -o root -g root -m 0755 /usr/local/libexec
sudo install -o root -g root -m 0755 "$BASE_SOURCE" "$BASE"
sudo "$BASE" apply | grep -q 'changed=1' || fail base_apply_failed
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

apply_output=''
if ! apply_output=$(sudo "$SERVICE" apply 2>&1); then
  printf '%s\n' "$apply_output" >&2
  sudo docker container ls --all --no-trunc >&2 || true
  sudo docker network ls >&2 || true
  for diagnostic_network in cloud-scope-cp00000001 cloud-scope-cp00000002 \
    cloud-scope-cp00000003 cloud-platform-egress; do
    printf 'DIAGNOSTIC network=%s\n' "$diagnostic_network" >&2
    sudo docker network inspect --format \
      '{{.Driver}}|{{.Internal}}|{{json .Options}}|{{json .IPAM.Config}}|{{json .Labels}}' \
      "$diagnostic_network" >&2 || true
  done
  for diagnostic_container in cp-dns-dev cp-dns-restricted cp-proxy-dev cp-proxy-restricted; do
    printf 'DIAGNOSTIC container=%s\n' "$diagnostic_container" >&2
    sudo docker inspect --format '{{json .State}}' "$diagnostic_container" >&2 || true
    sudo docker logs --tail 80 "$diagnostic_container" >&2 || true
    sudo docker inspect --format \
      'running={{.State.Running}} label={{index .Config.Labels "cloud.platform.managed"}}' \
      "$diagnostic_container" >&2 || true
    sudo docker port "$diagnostic_container" >&2 || true
  done
  sudo docker exec cp-dns-dev /coredns -version >&2 || printf '%s\n' 'DIAGNOSTIC dns-dev-version=FAIL' >&2
  sudo docker exec cp-dns-restricted /coredns -version >&2 ||
    printf '%s\n' 'DIAGNOSTIC dns-restricted-version=FAIL' >&2
  sudo iptables -w 5 -S CLOUD-PLATFORM-SVC >&2 || true
  sudo iptables -w 5 -S CLOUD-PLATFORM-EGRESS >&2 || true
  sudo iptables -w 5 -S DOCKER-USER >&2 || true
  sudo iptables -w 5 -S INPUT >&2 || true
  sudo ip6tables -w 5 -S DOCKER-USER >&2 || true
  sudo ip6tables -w 5 -S INPUT >&2 || true
  sudo sysctl net.ipv4.ip_forward net.ipv6.conf.all.forwarding >&2 || true
  sudo ss -Hlnptu >&2 || true
  fail first_apply_failed
fi
grep -q 'changed=1' <<<"$apply_output" || fail first_apply_change_missing
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
sudo "$BASE" apply >/dev/null
sudo "$SERVICE" apply | grep -q 'changed=1' || fail post_restart_reconcile_failed
sudo "$SERVICE" check >/dev/null || fail post_restart_check_failed

sudo "$SERVICE" rollback | grep -q 'NETWORK_SERVICES_ROLLBACK=PASS' || fail rollback_failed
for managed_file in "$SERVICE_MARKER" "$SYSCTL" "$SERVICE"; do
  sudo unlink -- "$managed_file"
done
sudo rm -f -- "$CONFIG/compose.yaml" \
  "$CONFIG/cp00000002/Corefile" "$CONFIG/cp00000002/records.hosts" \
  "$CONFIG/cp00000002/squid.conf" "$CONFIG/cp00000003/Corefile" \
  "$CONFIG/cp00000003/records.hosts" "$CONFIG/cp00000003/squid.conf"
sudo rmdir "$CONFIG/cp00000002" "$CONFIG/cp00000003" "$CONFIG" /etc/cloud-platform
sudo "$BASE" rollback >/dev/null
sudo unlink -- "$BASE"
[[ -z $(sudo docker container ls --all --quiet) ]] || fail containers_remained
[[ -z $(sudo docker image ls --all --quiet) ]] || fail images_remained
[[ -z $(sudo docker network ls --filter type=custom --quiet) ]] || fail networks_remained
[[ $(sysctl -n net.ipv4.ip_forward) == 0 ]] || fail forwarding_remained
trap - EXIT
printf '%s\n' \
  'NODE_NETWORK_SERVICES_VM_PASS apply=1 idempotence=0 dns=pass proxy=pass direct=denied restart=pass rollback=clean scope=disposable_only'
