#!/usr/bin/env bash
set -Eeuo pipefail

readonly CONFIRMATION=GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY
readonly ROOT=/workspace/cloud-infrastructure
readonly POLICY=$ROOT/platform/network/f1-2c-policy.example.yaml
readonly GENERATOR=$ROOT/scripts/generate_network_services.py
readonly COMPILER=$ROOT/scripts/compile_network_policy.py
readonly ENFORCEMENT=/usr/local/libexec/cloud-platform-network-enforcement
readonly IMAGE_SET=$ROOT/platform/network/f1-2c-service-images.yaml
readonly TMP_ROOT=${RUNNER_TEMP:?}/f1-2c-network-services
readonly EGRESS_NETWORK=cloud-platform-egress-fixture
readonly COREDNS_IMAGE=coredns/coredns@sha256:1ba6f47265602e2e50a9c4669e3a955e4298a0d30dc82f39293d4bf1a851e0ff
readonly SQUID_IMAGE=ubuntu/squid@sha256:1b8d2c7c46e435e022047e97cb7ac0b851c739f083427341cae7e4df1d99f5a3
readonly FIXTURE_IMAGE=busybox@sha256:7a3ebe5bfd1a4a19797d20b0c0bb39d44393e9a03fd852c0865b0f540d868df0

fail() {
  printf 'NETWORK_SERVICES_VM_TEST_FAIL reason=%s\n' "$1" >&2
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
[[ -x $GENERATOR && -x $COMPILER && -x $ENFORCEMENT && -f $IMAGE_SET ]] ||
  fail payload_missing
for network in cloud-scope-cp00000001 cloud-scope-cp00000002 cloud-scope-cp00000003; do
  sudo docker network inspect "$network" >/dev/null 2>&1 || fail "scope_missing=$network"
done

containers=(
  cp-dns-dev cp-dns-restricted cp-proxy-dev cp-proxy-restricted
  cp-origin-fixture cp-registry-fixture
)

cleanup() {
  local container image
  for container in "${containers[@]}"; do
    sudo docker rm --force "$container" >/dev/null 2>&1 || true
  done
  sudo docker network rm "$EGRESS_NETWORK" >/dev/null 2>&1 || true
  sudo "$ENFORCEMENT" apply >/dev/null 2>&1 || true
  for image in "$COREDNS_IMAGE" "$SQUID_IMAGE" "$FIXTURE_IMAGE"; do
    sudo docker image rm "$image" >/dev/null 2>&1 || true
  done
  sudo sysctl -q -w net.ipv4.ip_forward=0 >/dev/null 2>&1 || true
  rm -rf -- "$TMP_ROOT"
}
trap cleanup EXIT

rm -rf -- "$TMP_ROOT"
install -d -m 0700 "$TMP_ROOT/dev" "$TMP_ROOT/restricted" "$TMP_ROOT/origin"
printf '%s\n' NETWORK_SERVICES_FIXTURE_OK >"$TMP_ROOT/origin/index.html"

for interface in cp00000002 cp00000003; do
  scope=dev
  [[ $interface == cp00000003 ]] && scope=restricted
  python3 "$GENERATOR" "$POLICY" --component coredns --interface "$interface" \
    >"$TMP_ROOT/$scope/Corefile"
  python3 "$GENERATOR" "$POLICY" --component hosts --interface "$interface" \
    >"$TMP_ROOT/$scope/records.hosts"
  python3 "$GENERATOR" "$POLICY" --component squid --interface "$interface" \
    >"$TMP_ROOT/$scope/squid.conf"
done
python3 "$COMPILER" "$POLICY" --family ipv4 >"$TMP_ROOT/policy.v4"
python3 "$COMPILER" "$POLICY" --family ipv6 >"$TMP_ROOT/policy.v6"

grep -q 'admin.registry.shared.dev.internal' "$TMP_ROOT/restricted/records.hosts" ||
  fail restricted_dns_record_missing
! grep -q 'admin.registry.shared.dev.internal' "$TMP_ROOT/dev/records.hosts" ||
  fail hidden_dns_record_leaked
grep -q '^http_access deny all$' "$TMP_ROOT/dev/squid.conf" || fail proxy_default_deny_missing

for image in "$COREDNS_IMAGE" "$SQUID_IMAGE" "$FIXTURE_IMAGE"; do
  sudo docker pull "$image" >/dev/null
done
sudo docker network create --internal --subnet 172.31.250.0/24 "$EGRESS_NETWORK" >/dev/null

sudo docker run --detach --name cp-origin-fixture \
  --network "$EGRESS_NETWORK" --ip 172.31.250.10 \
  --network-alias security.ubuntu.com --network-alias api.github.com \
  --network-alias ghcr.io --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 32 --memory 32m --cpus 0.25 \
  --mount "type=bind,src=$TMP_ROOT/origin,dst=/www,readonly" \
  "$FIXTURE_IMAGE" httpd -f -p 80 -h /www >/dev/null

sudo docker run --detach --name cp-registry-fixture \
  --network cloud-scope-cp00000003 --ip 10.240.3.10 \
  --read-only --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 32 --memory 32m --cpus 0.25 \
  --mount "type=bind,src=$TMP_ROOT/origin,dst=/www,readonly" \
  "$FIXTURE_IMAGE" httpd -f -p 5000 -h /www >/dev/null

start_dns() {
  local name=$1 network=$2 ip=$3 scope=$4
  sudo docker run --detach --name "$name" --network "$network" --ip "$ip" \
    --read-only --cap-drop ALL --cap-add NET_BIND_SERVICE \
    --security-opt no-new-privileges --pids-limit 64 --memory 64m --cpus 0.25 \
    --mount "type=bind,src=$TMP_ROOT/$scope/Corefile,dst=/Corefile,readonly" \
    --mount "type=bind,src=$TMP_ROOT/$scope/records.hosts,dst=/etc/coredns/records.hosts,readonly" \
    "$COREDNS_IMAGE" -conf /Corefile >/dev/null
}

start_proxy() {
  local name=$1 network=$2 ip=$3 scope=$4
  sudo docker run --detach --name "$name" --network "$network" --ip "$ip" \
    --read-only --security-opt no-new-privileges --pids-limit 128 \
    --memory 256m --cpus 0.5 --tmpfs /run --tmpfs /var/log/squid --tmpfs /var/spool/squid \
    --mount "type=bind,src=$TMP_ROOT/$scope/squid.conf,dst=/etc/squid/squid.conf,readonly" \
    "$SQUID_IMAGE" >/dev/null
  sudo docker network connect "$EGRESS_NETWORK" "$name"
}

start_dns cp-dns-dev cloud-scope-cp00000002 10.240.2.2 dev
start_dns cp-dns-restricted cloud-scope-cp00000003 10.240.3.2 restricted
start_proxy cp-proxy-dev cloud-scope-cp00000002 10.240.2.3 dev
start_proxy cp-proxy-restricted cloud-scope-cp00000003 10.240.3.3 restricted

sudo iptables-restore -w 5 --noflush <"$TMP_ROOT/policy.v4"
sudo ip6tables-restore -w 5 --noflush <"$TMP_ROOT/policy.v6"
sudo sysctl -q -w net.ipv4.ip_forward=1 >/dev/null

for attempt in {1..30}; do
  if sudo docker exec cp-dns-dev /coredns -version >/dev/null 2>&1 &&
     sudo docker exec cp-proxy-dev pebble health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
[[ $(sudo docker inspect -f '{{.State.Running}}' cp-dns-dev) == true ]] || fail dns_not_running
[[ $(sudo docker inspect -f '{{.State.Running}}' cp-proxy-dev) == true ]] || fail proxy_not_running

probe() {
  local network=$1
  shift
  sudo docker run --rm --network "$network" --read-only --cap-drop ALL \
    --security-opt no-new-privileges --pids-limit 32 --memory 32m --cpus 0.25 \
    "$FIXTURE_IMAGE" "$@"
}

proxy_probe() {
  local network=$1 proxy=$2 url=$3
  sudo docker run --rm --network "$network" --read-only --cap-drop ALL \
    --security-opt no-new-privileges --pids-limit 32 --memory 32m --cpus 0.25 \
    --env "http_proxy=http://$proxy:3128" \
    "$FIXTURE_IMAGE" wget -T 3 -qO- -Y on "$url"
}

probe cloud-scope-cp00000002 nslookup registry.shared.dev.internal 10.240.2.2 |
  grep -q '10.240.3.10' || fail dev_dns_shared_record_failed
if probe cloud-scope-cp00000002 nslookup admin.registry.shared.dev.internal 10.240.2.2 \
  >/dev/null 2>&1; then
  fail hidden_dns_record_resolved
fi
probe cloud-scope-cp00000003 nslookup admin.registry.shared.dev.internal 10.240.3.2 |
  grep -q '10.240.3.11' || fail restricted_dns_admin_record_failed

proxy_probe cloud-scope-cp00000002 10.240.2.3 \
  http://security.ubuntu.com/index.html |
  grep -q NETWORK_SERVICES_FIXTURE_OK || fail development_proxy_allow_failed
if proxy_probe cloud-scope-cp00000003 10.240.3.3 \
  http://security.ubuntu.com/index.html >/dev/null 2>&1; then
  fail restricted_proxy_allowed_unlisted_destination
fi
if probe cloud-scope-cp00000002 wget -qO- http://172.31.250.10/index.html \
  >/dev/null 2>&1; then
  fail workload_reached_direct_egress
fi

probe cloud-scope-cp00000002 wget -qO- http://10.240.3.10:5000/index.html |
  grep -q NETWORK_SERVICES_FIXTURE_OK || fail explicit_shared_service_grant_failed
python3 - "$POLICY" "$TMP_ROOT/no-grant.yaml" <<'PY'
import pathlib, sys, yaml
source, destination = map(pathlib.Path, sys.argv[1:])
raw = yaml.safe_load(source.read_text(encoding="utf-8"))
raw["shared_service_grants"] = []
destination.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
PY
python3 "$COMPILER" "$TMP_ROOT/no-grant.yaml" --family ipv4 >"$TMP_ROOT/no-grant.v4"
sudo iptables-restore -w 5 --noflush <"$TMP_ROOT/no-grant.v4"
if probe cloud-scope-cp00000002 wget -T 3 -qO- \
  http://10.240.3.10:5000/index.html >/dev/null 2>&1; then
  fail revoked_grant_remained_reachable
fi

sudo docker stop cp-dns-dev >/dev/null
if probe cloud-scope-cp00000002 nslookup registry.shared.dev.internal 10.240.2.2 \
  >/dev/null 2>&1; then
  fail dns_dependency_failure_did_not_close
fi
sudo docker stop cp-proxy-dev >/dev/null
if proxy_probe cloud-scope-cp00000002 10.240.2.3 \
  http://security.ubuntu.com/index.html >/dev/null 2>&1; then
  fail proxy_dependency_failure_did_not_close
fi

for container in "${containers[@]}"; do
  sudo docker rm --force "$container" >/dev/null 2>&1 || true
done
sudo docker network rm "$EGRESS_NETWORK" >/dev/null
sudo "$ENFORCEMENT" apply >/dev/null
sudo sysctl -q -w net.ipv4.ip_forward=0 >/dev/null
for image in "$COREDNS_IMAGE" "$SQUID_IMAGE" "$FIXTURE_IMAGE"; do
  sudo docker image rm "$image" >/dev/null
done
rm -rf -- "$TMP_ROOT"
trap - EXIT
printf '%s\n' \
  'NETWORK_SERVICES_VM_TEST_PASS scoped_dns=pass hidden_record=denied proxy_allow=pass proxy_profile_deny=pass direct_egress=denied grant=pass revoked_grant=denied dependency_failure=closed cleanup=clean scope=disposable_only'
