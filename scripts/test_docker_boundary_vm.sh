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
[[ -f /etc/os-release && ! -L /etc/os-release ]] || refuse invalid_os_release

# shellcheck disable=SC1091
source /etc/os-release
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

CURRENT_STAGE=implementation_pending
fail harness_implementation_not_yet_complete
