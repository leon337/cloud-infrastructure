#!/usr/bin/env bash
set -euo pipefail

# This harness mutates package, systemd, firewall and Docker state. It is safe
# only on the fresh GitHub-hosted VM selected by docker-boundary-ci.yml. The
# gate deliberately runs before sudo, cleanup, package operations or writes.
REPOSITORY_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
PRIVILEGED_CONFIRMATION=GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY
EXPECTED_REPOSITORY=leon337/cloud-infrastructure
EXPECTED_WORKSPACE=/home/runner/work/cloud-infrastructure/cloud-infrastructure
DOCKER_APT_PREFERENCE_SOURCE=platform/docker/cloud-platform-docker.pref
DOCKER_APT_PREFERENCE_DESTINATION=/etc/apt/preferences.d/cloud-platform-docker.pref
BUNDLE_ROOT=/workspace/cloud-infrastructure
BUNDLE_ARCHIVE=${RUNNER_TEMP:-/tmp}/cloud-infrastructure-docker-boundary.tar
ANSIBLE_ROOT=$BUNDLE_ROOT/automation/ansible
INVENTORY=$ANSIBLE_ROOT/inventory/docker-test/hosts.yml
APPLY_PLAYBOOK=playbooks/docker-runtime.yml
ROLLBACK_PLAYBOOK=playbooks/rollback-docker-runtime.yml
TEST_CONFIRMATION=platform_docker_test_destructive_confirm=true
ROLLBACK_CONFIRMATION=platform_docker_runtime_rollback_confirm=true
DPKG_STATUS_FORMAT="\${db:Status-Abbrev}"
DPKG_SURFACE_FORMAT="\${Package}|\${db:Status-Abbrev}|\${Version}\\n"
CURRENT_STAGE=privileged_gate
GATE_ONLY=false

refuse() {
  printf '%s\n' \
    "DOCKER_BOUNDARY_VM_TEST_REFUSED stage=$CURRENT_STAGE reason=$*" >&2
  exit 64
}

fail() {
  printf '%s\n' \
    "DOCKER_BOUNDARY_VM_TEST_FAIL stage=$CURRENT_STAGE reason=$*" >&2
  exit 1
}

if (($# > 1)); then
  refuse unexpected_arguments
fi
if (($# == 1)); then
  [[ $1 == --gate-only ]] || refuse "unexpected_argument=$1"
  GATE_ONLY=true
fi

HOST_SHORT=$(hostname --short 2>/dev/null || hostname)
case "${HOST_SHORT,,}" in
  node-01 | vmi3506102)
    refuse "real_dev_node host=$HOST_SHORT"
    ;;
esac

[[ ${DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM:-} == "$PRIVILEGED_CONFIRMATION" ]] ||
  refuse missing_exact_confirmation
[[ ${GITHUB_ACTIONS:-} == true ]] || refuse not_github_actions
[[ ${CI:-} == true ]] || refuse not_ci
[[ ${RUNNER_ENVIRONMENT:-} == github-hosted ]] || refuse not_github_hosted
[[ ${RUNNER_OS:-} == Linux ]] || refuse unexpected_runner_os
[[ ${RUNNER_ARCH:-} == X64 ]] || refuse unexpected_runner_arch
[[ ${ImageOS:-} == ubuntu24 ]] || refuse unexpected_image_os
[[ ${GITHUB_SERVER_URL:-} == https://github.com ]] || refuse unexpected_github_server
[[ ${GITHUB_REPOSITORY:-} == "$EXPECTED_REPOSITORY" ]] || refuse unexpected_repository
case "${GITHUB_EVENT_NAME:-}" in
  pull_request | push | workflow_dispatch) ;;
  *) refuse unexpected_github_event ;;
esac
[[ $(id -u) -ne 0 ]] || refuse runner_must_not_start_as_root
[[ $(id -un) == runner ]] || refuse unexpected_runner_user
[[ ${HOME:-} == /home/runner ]] || refuse unexpected_runner_home
OS_RELEASE=/etc/os-release
[[ -f $OS_RELEASE ]] || refuse invalid_os_release
if [[ -L $OS_RELEASE ]]; then
  [[ $(realpath -- "$OS_RELEASE") == /usr/lib/os-release ]] ||
    refuse unexpected_os_release_link
  [[ -f /usr/lib/os-release && ! -L /usr/lib/os-release ]] ||
    refuse invalid_canonical_os_release
  OS_RELEASE=/usr/lib/os-release
fi
[[ $(stat -c '%u:%a' -- "$OS_RELEASE") == 0:644 ]] ||
  refuse unsafe_os_release_metadata

# shellcheck disable=SC1090
source "$OS_RELEASE"
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 24.04 ]] ||
  refuse unexpected_distribution
[[ -d /run/systemd/system ]] || refuse systemd_not_running
systemd-detect-virt --quiet --vm || refuse runner_is_not_a_vm
[[ -d /opt/hostedtoolcache && ! -L /opt/hostedtoolcache ]] ||
  refuse hosted_toolcache_absent
[[ -d ${RUNNER_TEMP:-} && ! -L ${RUNNER_TEMP:-} ]] || refuse invalid_runner_temp
[[ ${RUNNER_TEMP:-} == /home/runner/work/_temp ]] || refuse unexpected_runner_temp
[[ ${GITHUB_WORKSPACE:-} == "$EXPECTED_WORKSPACE" ]] || refuse unexpected_workspace
[[ $(realpath -- "$REPOSITORY_ROOT") == "$EXPECTED_WORKSPACE" ]] ||
  refuse checkout_path_mismatch
sudo -n true >/dev/null 2>&1 || refuse passwordless_sudo_unavailable

printf '%s\n' \
  "DOCKER_BOUNDARY_VM_GATE_ACCEPTED host=$HOST_SHORT image=ubuntu24 boundary=github-hosted-vm"

if [[ $GATE_ONLY == true ]]; then
  printf '%s\n' 'DOCKER_BOUNDARY_VM_GATE_ONLY_PASS no_mutation=true'
  exit 0
fi

remove_disposable_tree() {
  local target=$1

  case "$target" in
    /var/lib/docker | /var/lib/containerd | /etc/docker | /etc/containerd | \
      /run/docker | /run/containerd | \
      /etc/systemd/system/docker.service.d | \
      /etc/systemd/system/docker.socket.d | \
      /etc/systemd/system/containerd.service.d | \
      "$BUNDLE_ROOT") ;;
    *) fail "unreviewed_tree_cleanup=$target" ;;
  esac
  if [[ -L $target ]]; then
    sudo unlink -- "$target"
  elif [[ -d $target ]]; then
    if sudo findmnt --noheadings --mountpoint "$target" >/dev/null 2>&1; then
      fail "cleanup_target_is_mountpoint=$target"
    fi
    sudo find "$target" -xdev -depth -delete
  elif [[ -e $target ]]; then
    sudo unlink -- "$target"
  fi
}

remove_exact_path() {
  local target=$1

  case "$target" in
    /run/docker.sock | \
      /etc/apt/keyrings/docker.asc | \
      /etc/apt/keyrings/docker.gpg | \
      /etc/apt/sources.list.d/docker.list | \
      /etc/apt/sources.list.d/docker.sources | \
      /etc/apt/preferences.d/cloud-platform-docker.pref | \
      /usr/share/keyrings/docker-archive-keyring.gpg | \
      /etc/systemd/system/docker.service | \
      /etc/systemd/system/docker.socket | \
      /etc/systemd/system/containerd.service) ;;
    *) fail "unreviewed_path_cleanup=$target" ;;
  esac
  if [[ -e $target || -L $target ]]; then
    sudo unlink -- "$target"
  fi
}

run_playbook() {
  local log_path=$1
  shift

  (
    cd "$ANSIBLE_ROOT"
    ansible-playbook -i "$INVENTORY" "$@"
  ) 2>&1 | tee "$log_path"
}

managed_surface_digest() {
  {
    local path package unit
    for path in \
      /etc/cloud-platform-docker-runtime.managed \
      /etc/apt/keyrings/docker.asc \
      /etc/apt/sources.list.d/docker.sources \
      /etc/apt/preferences.d/cloud-platform-docker.pref \
      /etc/docker \
      /etc/systemd/system/docker.service.d \
      /etc/systemd/system/docker.socket.d \
      /etc/systemd/system/containerd.service.d \
      /var/lib/cloud-platform/runtime-boundaries \
      /var/lib/docker \
      /var/lib/containerd \
      /run/docker.sock; do
      if sudo test -e "$path" || sudo test -L "$path"; then
        sudo stat --printf='%n|%F|%u|%g|%a|%d|%i|%s\n' -- "$path"
      else
        printf '%s|ABSENT\n' "$path"
      fi
    done
    for package in \
      docker-ce docker-ce-cli containerd.io docker-buildx-plugin \
      docker-compose-plugin; do
      dpkg-query -W -f="$DPKG_SURFACE_FORMAT" \
        "$package" 2>/dev/null || printf '%s|ABSENT\n' "$package"
    done
    getent group docker || printf '%s\n' 'docker-group|ABSENT'
    for unit in docker.service docker.socket containerd.service; do
      printf '%s|' "$unit"
      systemctl is-active "$unit" 2>/dev/null || true
    done
  } | sha256sum | awk '{print $1}'
}

expect_refusal() {
  local label=$1
  shift
  local before after log_path

  CURRENT_STAGE="refusal_$label"
  before=$(managed_surface_digest)
  log_path="$RUNNER_TEMP/docker-boundary-refusal-$label.log"
  if run_playbook "$log_path" "$@"; then
    fail "expected_refusal_passed=$label"
  fi
  after=$(managed_surface_digest)
  [[ $before == "$after" ]] || fail "refusal_mutated_surface=$label"
  grep -Eq 'FAILED|fatal:' "$log_path" || fail "refusal_not_observed=$label"
  printf 'DOCKER_BOUNDARY_REFUSAL_PASS scenario=%s no_mutation=true\n' "$label"
}

capture_network_state() {
  local prefix=$1

  # Interface flags/qdisc on a hosted runner may change transiently without an
  # interface being added. The contract is the stable, exact interface set;
  # routes, forwarding, listeners and firewall state are checked separately.
  ip -o link show |
    awk -F': ' '{name=$2; sub(/@.*/, "", name); print name}' |
    LC_ALL=C sort >"$prefix.interfaces"
  ip -4 route show table all >"$prefix.routes4"
  ip -6 route show table all >"$prefix.routes6"
  sysctl -n net.ipv4.ip_forward >"$prefix.forward4"
  sysctl -n net.ipv6.conf.all.forwarding >"$prefix.forward6"
  ss -H -lntup >"$prefix.listeners"
  sudo iptables-save | tee "$prefix.iptables4" >/dev/null
  sudo ip6tables-save | tee "$prefix.iptables6" >/dev/null
  sudo nft list ruleset | tee "$prefix.nft" >/dev/null
  if command -v ufw >/dev/null 2>&1; then
    sudo ufw status verbose | tee "$prefix.ufw" >/dev/null
  else
    printf '%s\n' 'UFW_NOT_INSTALLED' >"$prefix.ufw"
  fi
}

normalize_non_docker_iptables() {
  local source=$1
  local destination=$2

  sed -E '/docker/I d' "$source" >"$destination"
}

compare_network_invariants() {
  local before=$1
  local after=$2
  local category

  for category in interfaces routes4 routes6 forward4 forward6 listeners ufw; do
    if ! cmp -s "$before.$category" "$after.$category"; then
      printf 'DOCKER_BOUNDARY_NETWORK_DIFF category=%s\n' "$category" >&2
      diff -u "$before.$category" "$after.$category" >&2 || true
      fail "network_invariant_changed=$category"
    fi
  done
  normalize_non_docker_iptables \
    "$before.iptables4" "$before.iptables4.non-docker"
  normalize_non_docker_iptables \
    "$after.iptables4" "$after.iptables4.non-docker"
  normalize_non_docker_iptables \
    "$before.iptables6" "$before.iptables6.non-docker"
  normalize_non_docker_iptables \
    "$after.iptables6" "$after.iptables6.non-docker"
  if ! cmp -s "$before.iptables4.non-docker" "$after.iptables4.non-docker"; then
    printf '%s\n' 'DOCKER_BOUNDARY_NETWORK_DIFF category=non_docker_ipv4_rules' >&2
    diff -u "$before.iptables4.non-docker" \
      "$after.iptables4.non-docker" >&2 || true
    fail non_docker_ipv4_rules_changed
  fi
  if ! cmp -s "$before.iptables6.non-docker" "$after.iptables6.non-docker"; then
    printf '%s\n' 'DOCKER_BOUNDARY_NETWORK_DIFF category=non_docker_ipv6_rules' >&2
    diff -u "$before.iptables6.non-docker" \
      "$after.iptables6.non-docker" >&2 || true
    fail non_docker_ipv6_rules_changed
  fi
  ! grep -Eiq 'table (ip|ip6|inet) docker-bridges' "$after.nft" ||
    fail experimental_native_nftables_backend_detected
}

cleanup_foundation_fixture() {
  local path

  for path in \
    /etc/cloud-platform-foundation.managed \
    /etc/tmpfiles.d/cloud-platform.conf \
    /etc/systemd/system/cloud-platform.slice \
    /etc/systemd/system/cloud-workloads.slice; do
    sudo unlink -- "$path"
  done
  sudo systemctl daemon-reload
  sudo rmdir /run/cloud-platform/credentials
  sudo rmdir /run/cloud-platform
  for path in \
    /var/cache/cloud-platform \
    /var/log/cloud-platform \
    /var/lib/cloud-platform \
    /etc/cloud-platform; do
    sudo rmdir "$path"
  done
  sudo userdel platform-core
  sudo groupdel cloud-platform
}

CURRENT_STAGE=prepare_bundle
[[ ! -e /workspace && ! -L /workspace ]] || refuse workspace_already_exists
RUNNER_GROUP=$(id -gn)
git -C "$REPOSITORY_ROOT" archive --format=tar HEAD --output="$BUNDLE_ARCHIVE"
sudo install -d -o runner -g "$RUNNER_GROUP" -m 0755 /workspace
install -d -m 0755 "$BUNDLE_ROOT"
tar -xf "$BUNDLE_ARCHIVE" -C "$BUNDLE_ROOT"
[[ -f "$BUNDLE_ROOT/$DOCKER_APT_PREFERENCE_SOURCE" ]] ||
  fail missing_pinned_apt_payload
[[ $DOCKER_APT_PREFERENCE_DESTINATION == \
  /etc/apt/preferences.d/cloud-platform-docker.pref ]] ||
  fail apt_preference_destination_drift

CURRENT_STAGE=sanitize_disposable_runner
for unit in docker.service docker.socket containerd.service; do
  if systemctl cat "$unit" >/dev/null 2>&1; then
    sudo systemctl disable --now "$unit"
  fi
done

installed_runner_packages=()
for package in \
  docker-ce docker-ce-cli docker-ce-rootless-extras docker-buildx-plugin \
  docker-compose-plugin containerd.io docker.io docker-doc docker-compose \
  podman-docker containerd runc moby-engine moby-cli moby-buildx \
  moby-compose moby-containerd moby-runc; do
  # Purge both installed packages and dpkg's residual-config (rc) records.
  # The role deliberately requires a truly absent first-apply surface.
  if dpkg-query -W -f="$DPKG_STATUS_FORMAT" "$package" >/dev/null 2>&1; then
    installed_runner_packages+=("$package")
  fi
done
if ((${#installed_runner_packages[@]} > 0)); then
  sudo apt-get purge --yes --no-install-recommends \
    "${installed_runner_packages[@]}"
fi

for path in \
  /var/lib/docker /var/lib/containerd /etc/docker /etc/containerd \
  /run/docker /run/containerd; do
  remove_disposable_tree "$path"
done
for path in \
  /run/docker.sock \
  /etc/apt/keyrings/docker.asc \
  /etc/apt/keyrings/docker.gpg \
  /etc/apt/sources.list.d/docker.list \
  /etc/apt/sources.list.d/docker.sources \
  /etc/apt/preferences.d/cloud-platform-docker.pref \
  /usr/share/keyrings/docker-archive-keyring.gpg \
  /etc/systemd/system/docker.service \
  /etc/systemd/system/docker.socket \
  /etc/systemd/system/containerd.service; do
  remove_exact_path "$path"
done
for path in \
  /etc/systemd/system/docker.service.d \
  /etc/systemd/system/docker.socket.d \
  /etc/systemd/system/containerd.service.d; do
  remove_disposable_tree "$path"
done
sudo systemctl daemon-reload

# GitHub's disposable image can retain docker0 after the preinstalled Docker
# packages and state are removed. Establish a pristine boundary baseline: only
# delete that exact, canonical Docker bridge and refuse an unexpected link type.
if ip link show dev docker0 >/dev/null 2>&1; then
  ip -d link show dev docker0 | grep -Eq '(^|[[:space:]])bridge([[:space:]]|$)' ||
    fail preinstalled_docker0_is_not_a_bridge
  sudo ip link delete dev docker0 type bridge
  ! ip link show dev docker0 >/dev/null 2>&1 ||
    fail preinstalled_docker0_survived_cleanup
  printf '%s\n' 'DOCKER_BOUNDARY_RUNNER_CLEANUP interface=docker0 type=bridge result=removed'
fi

if docker_group=$(getent group docker); then
  docker_gid=$(cut -d: -f3 <<<"$docker_group")
  docker_members=${docker_group##*:}
  docker_primary_accounts=$(
    getent passwd | awk -F: -v gid="$docker_gid" '$4 == gid {print $1}'
  )
  [[ -z $docker_members || $docker_members == runner ]] ||
    fail runner_docker_group_has_unexpected_members
  [[ -z $docker_primary_accounts || $docker_primary_accounts == runner ]] ||
    fail runner_docker_group_has_unexpected_primary_account
  if [[ $docker_primary_accounts == runner ]]; then
    ! getent group cloud-ci-runner >/dev/null || fail fixture_group_collision
    sudo groupadd --system cloud-ci-runner
    sudo usermod --gid cloud-ci-runner runner
  fi
  if [[ $docker_members == runner ]]; then
    sudo gpasswd --delete runner docker
  fi
  sudo groupdel docker
fi
RUNNER_GROUP=$(id -gn runner)

CURRENT_STAGE=provision_foundation_fixture
export DOCKER_BOUNDARY_FIXTURE_CONFIRM=DOCKER_BOUNDARY_FIXTURE_ON_GATED_VM_ONLY
export DOCKER_BOUNDARY_BUNDLE_ROOT=$BUNDLE_ROOT
sudo --preserve-env=DOCKER_BOUNDARY_FIXTURE_CONFIRM,DOCKER_BOUNDARY_BUNDLE_ROOT \
  "$BUNDLE_ROOT/tests/fixtures/docker-boundary/provision-foundation.sh"

export GITHUB_WORKSPACE=$BUNDLE_ROOT
export ANSIBLE_CONFIG=$ANSIBLE_ROOT/ansible.cfg
NETWORK_BEFORE=$RUNNER_TEMP/docker-boundary-network-before
NETWORK_AFTER=$RUNNER_TEMP/docker-boundary-network-after
capture_network_state "$NETWORK_BEFORE"

expect_refusal missing_confirmation \
  "$APPLY_PLAYBOOK" --check --diff
expect_refusal environment_override \
  "$APPLY_PLAYBOOK" --check --diff \
  -e "$TEST_CONFIRMATION" -e platform_environment=dev
expect_refusal immutable_path_override \
  "$APPLY_PLAYBOOK" --check --diff \
  -e "$TEST_CONFIRMATION" -e platform_docker_marker=/tmp/redirected-marker

CURRENT_STAGE=initial_check_mode
surface_before_check=$(managed_surface_digest)
run_playbook "$RUNNER_TEMP/docker-boundary-check.log" \
  "$APPLY_PLAYBOOK" --check --diff -e "$TEST_CONFIRMATION"
surface_after_check=$(managed_surface_digest)
[[ $surface_before_check == "$surface_after_check" ]] ||
  fail check_mode_mutated_managed_surface
grep -Eq 'changed=[1-9][0-9]* .*failed=0' \
  "$RUNNER_TEMP/docker-boundary-check.log" ||
  fail check_mode_recap_missing
printf '%s\n' 'DOCKER_BOUNDARY_CHECK_MODE_PASS no_mutation=true'

CURRENT_STAGE=first_apply
run_playbook "$RUNNER_TEMP/docker-boundary-first-apply.log" \
  "$APPLY_PLAYBOOK" --diff -e "$TEST_CONFIRMATION"
grep -Eq 'changed=[1-9][0-9]* .*failed=0' \
  "$RUNNER_TEMP/docker-boundary-first-apply.log" ||
  fail first_apply_recap_missing

CURRENT_STAGE=second_reconcile
run_playbook "$RUNNER_TEMP/docker-boundary-second-apply.log" \
  "$APPLY_PLAYBOOK" --diff -e "$TEST_CONFIRMATION"
grep -Eq 'changed=0 .*failed=0' \
  "$RUNNER_TEMP/docker-boundary-second-apply.log" ||
  fail second_reconcile_not_idempotent

CURRENT_STAGE=security_and_network_postconditions
[[ $(stat -c '%U:%G:%a' /run/docker.sock) == root:root:600 ]] ||
  fail socket_boundary_changed
if sudo -u runner docker info >/dev/null 2>&1; then
  fail runner_reached_docker_socket
fi
if sudo -u platform-core docker info >/dev/null 2>&1; then
  fail platform_core_reached_docker_socket
fi
[[ -z $(sudo docker container ls --all --quiet) ]] || fail containers_present
[[ -z $(sudo docker image ls --all --quiet) ]] || fail images_present
[[ -z $(sudo docker volume ls --quiet) ]] || fail volumes_present
[[ -z $(sudo docker network ls --filter type=custom --quiet) ]] ||
  fail custom_networks_present
[[ -z $(sudo docker buildx du --format '{{.ID}}') ]] || fail build_cache_present
[[ $(sudo docker info --format '{{.Swarm.LocalNodeState}}') == inactive ]] ||
  fail swarm_active
! ip -o link show | grep -Eq ': (docker0|br-[^:]+):' ||
  fail docker_bridge_present
! ss -H -lnt | grep -Eq ':(2375|2376)[[:space:]]' ||
  fail docker_tcp_api_present

capture_network_state "$NETWORK_AFTER"
compare_network_invariants "$NETWORK_BEFORE" "$NETWORK_AFTER"

CURRENT_STAGE=restart_and_reconcile
sudo systemctl restart containerd.service docker.service
run_playbook "$RUNNER_TEMP/docker-boundary-post-restart.log" \
  "$APPLY_PLAYBOOK" --diff -e "$TEST_CONFIRMATION"
grep -Eq 'changed=0 .*failed=0' \
  "$RUNNER_TEMP/docker-boundary-post-restart.log" ||
  fail post_restart_reconcile_not_idempotent

expect_refusal rollback_missing_confirmation \
  "$ROLLBACK_PLAYBOOK" --diff -e "$TEST_CONFIRMATION"

CURRENT_STAGE=marker_refusal_setup
MARKER_BACKUP=$RUNNER_TEMP/cloud-platform-docker-runtime.managed
sudo install -o runner -g "$RUNNER_GROUP" -m 0600 \
  /etc/cloud-platform-docker-runtime.managed "$MARKER_BACKUP"
printf '%s' 'tampered-marker' |
  sudo tee /etc/cloud-platform-docker-runtime.managed >/dev/null
expect_refusal rollback_marker_drift \
  "$ROLLBACK_PLAYBOOK" --diff \
  -e "$TEST_CONFIRMATION" -e "$ROLLBACK_CONFIRMATION"
sudo install -o root -g root -m 0600 \
  "$MARKER_BACKUP" /etc/cloud-platform-docker-runtime.managed

CURRENT_STAGE=group_refusal_setup
sudo usermod --append --groups docker runner
expect_refusal rollback_group_member \
  "$ROLLBACK_PLAYBOOK" --diff \
  -e "$TEST_CONFIRMATION" -e "$ROLLBACK_CONFIRMATION"
sudo gpasswd --delete runner docker

CURRENT_STAGE=object_refusal_setup
sudo docker volume create cloud-platform-rollback-refusal >/dev/null
expect_refusal rollback_docker_object \
  "$ROLLBACK_PLAYBOOK" --diff \
  -e "$TEST_CONFIRMATION" -e "$ROLLBACK_CONFIRMATION"
sudo docker volume rm cloud-platform-rollback-refusal >/dev/null

CURRENT_STAGE=tree_refusal_setup
sudo install -o root -g root -m 0600 /dev/null \
  /var/lib/docker/cloud-platform-rollback-refusal
expect_refusal rollback_tree_drift \
  "$ROLLBACK_PLAYBOOK" --diff \
  -e "$TEST_CONFIRMATION" -e "$ROLLBACK_CONFIRMATION"
sudo unlink -- /var/lib/docker/cloud-platform-rollback-refusal

CURRENT_STAGE=rollback_check_mode
surface_before_check=$(managed_surface_digest)
run_playbook "$RUNNER_TEMP/docker-boundary-rollback-check.log" \
  "$ROLLBACK_PLAYBOOK" --check --diff \
  -e "$TEST_CONFIRMATION" -e "$ROLLBACK_CONFIRMATION"
surface_after_check=$(managed_surface_digest)
[[ $surface_before_check == "$surface_after_check" ]] ||
  fail rollback_check_mode_mutated_managed_surface

CURRENT_STAGE=rollback_apply
run_playbook "$RUNNER_TEMP/docker-boundary-rollback.log" \
  "$ROLLBACK_PLAYBOOK" --diff \
  -e "$TEST_CONFIRMATION" -e "$ROLLBACK_CONFIRMATION"
[[ ! -e /etc/cloud-platform-docker-runtime.managed ]] ||
  fail marker_survived_rollback
[[ ! -e /var/lib/docker && ! -e /var/lib/containerd ]] ||
  fail runtime_roots_survived_rollback
! getent group docker >/dev/null || fail docker_group_survived_rollback
for package in \
  docker-ce docker-ce-cli containerd.io docker-buildx-plugin \
  docker-compose-plugin; do
  if dpkg-query -W -f="$DPKG_STATUS_FORMAT" "$package" 2>/dev/null |
    grep -qx 'ii '; then
    fail "package_survived_rollback=$package"
  fi
done
[[ -f /etc/cloud-platform-foundation.managed ]] ||
  fail foundation_marker_removed_by_docker_rollback

CURRENT_STAGE=fixture_cleanup
cleanup_foundation_fixture
remove_disposable_tree "$BUNDLE_ROOT"
sudo rmdir /workspace
unlink -- "$BUNDLE_ARCHIVE"

printf '%s\n' \
  'DOCKER_BOUNDARY_VM_TEST_PASS check=clean apply=pass idempotence=changed_0 restart=pass refusals=7 rollback=clean cleanup=pass'
