#!/usr/bin/env bash
set -euo pipefail

# Called only after the enclosing disposable-VM gate. This fixture creates the
# exact minimal SLICE-001 prerequisite and never represents a DEV-node apply.
EXPECTED_ROOT=/workspace/cloud-infrastructure
CONFIRMATION=DOCKER_BOUNDARY_FIXTURE_ON_GATED_VM_ONLY
FOUNDATION_MARKER_CONTENT=$'managed_by=cloud-infrastructure\nslice=SLICE-001\nschema=1\nenvironment=test\nnode=node-01'

[[ $(id -u) -eq 0 ]] || {
  printf '%s\n' 'DOCKER_BOUNDARY_FIXTURE_REFUSED reason=root_required' >&2
  exit 64
}
[[ ${DOCKER_BOUNDARY_FIXTURE_CONFIRM:-} == "$CONFIRMATION" ]] || {
  printf '%s\n' 'DOCKER_BOUNDARY_FIXTURE_REFUSED reason=confirmation_missing' >&2
  exit 64
}
[[ ${DOCKER_BOUNDARY_BUNDLE_ROOT:-} == "$EXPECTED_ROOT" ]] || {
  printf '%s\n' 'DOCKER_BOUNDARY_FIXTURE_REFUSED reason=bundle_root_mismatch' >&2
  exit 64
}
[[ -f "$EXPECTED_ROOT/platform/systemd/cloud-platform.slice" ]] || exit 65
[[ -f "$EXPECTED_ROOT/platform/systemd/cloud-workloads.slice" ]] || exit 65
[[ -f "$EXPECTED_ROOT/platform/tmpfiles.d/cloud-platform.conf" ]] || exit 65

! getent passwd platform-core >/dev/null || exit 65
! getent group cloud-platform >/dev/null || exit 65
[[ ! -e /etc/cloud-platform-foundation.managed ]] || exit 65

groupadd --system cloud-platform
useradd \
  --system \
  --gid cloud-platform \
  --comment 'Cloud Platform unprivileged control-plane identity' \
  --home-dir /nonexistent \
  --no-create-home \
  --shell /usr/sbin/nologin \
  platform-core
passwd --lock platform-core >/dev/null

install -d -o root -g cloud-platform -m 0750 \
  /etc/cloud-platform \
  /var/lib/cloud-platform \
  /var/log/cloud-platform \
  /var/cache/cloud-platform \
  /run/cloud-platform
install -d -o root -g root -m 0700 /run/cloud-platform/credentials
install -o root -g root -m 0644 \
  "$EXPECTED_ROOT/platform/tmpfiles.d/cloud-platform.conf" \
  /etc/tmpfiles.d/cloud-platform.conf
install -o root -g root -m 0644 \
  "$EXPECTED_ROOT/platform/systemd/cloud-platform.slice" \
  /etc/systemd/system/cloud-platform.slice
install -o root -g root -m 0644 \
  "$EXPECTED_ROOT/platform/systemd/cloud-workloads.slice" \
  /etc/systemd/system/cloud-workloads.slice
install -o root -g root -m 0600 /dev/null /etc/cloud-platform-foundation.managed
printf '%s' "$FOUNDATION_MARKER_CONTENT" \
  > /etc/cloud-platform-foundation.managed
systemctl daemon-reload
systemd-tmpfiles --create /etc/tmpfiles.d/cloud-platform.conf

printf '%s\n' 'DOCKER_BOUNDARY_FOUNDATION_FIXTURE_READY slice=SLICE-001 environment=test'
