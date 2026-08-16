#!/usr/bin/env bash
set -euo pipefail

# Docker needs a privileged container to run this systemd/cgroup fixture reliably.
# That is root-equivalent on the Docker host, so the harness is gated to an
# explicitly acknowledged disposable VM and never bind-mounts the checkout.
REPOSITORY_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
DOCKERFILE="$REPOSITORY_ROOT/tests/fixtures/foundation-systemd/Dockerfile"
CONTAINER_REPOSITORY_ROOT=/workspace/cloud-infrastructure
FOUNDATION_MARKER=/etc/cloud-platform-foundation.managed
PRIVILEGED_CONFIRMATION=DISPOSABLE_VM_ONLY
CURRENT_STAGE=preflight
HARNESS_TMP_DIR=
IMAGE=
CONTAINER=
check_output=
first_output=
second_output=
rollback_output=
check_mode_before=
check_mode_after=
partial_check_output=
partial_check_before=
partial_check_after=
BUNDLE_SOURCE_COUNT=0

fail() {
  printf '%s\n' "FOUNDATION_CONTAINER_TEST_FAIL stage=$CURRENT_STAGE reason=$*" >&2
  exit 1
}

cleanup() {
  local original_status=$?
  local cleanup_status=0

  trap - EXIT INT TERM
  set +e

  if [[ -n "$CONTAINER" ]] && docker container inspect "$CONTAINER" >/dev/null 2>&1; then
    docker container rm --force "$CONTAINER" >/dev/null 2>&1 || cleanup_status=1
  fi
  if [[ -n "$IMAGE" ]] && docker image inspect "$IMAGE" >/dev/null 2>&1; then
    docker image rm --force "$IMAGE" >/dev/null 2>&1 || cleanup_status=1
  fi
  if [[ -n "$HARNESS_TMP_DIR" ]]; then
    case "$HARNESS_TMP_DIR" in
      /tmp/cloud-platform-foundation-test.*)
        rm -rf -- "$HARNESS_TMP_DIR" || cleanup_status=1
        ;;
      *)
        printf '%s\n' \
          "FOUNDATION_CONTAINER_TEST_CLEANUP_REFUSED unexpected_path=$HARNESS_TMP_DIR" >&2
        cleanup_status=1
        ;;
    esac
  fi

  if ((original_status == 0 && cleanup_status != 0)); then
    printf '%s\n' 'FOUNDATION_CONTAINER_TEST_FAIL stage=cleanup' >&2
    original_status=1
  elif ((original_status != 0)); then
    printf '%s\n' \
      "FOUNDATION_CONTAINER_TEST_ABORTED stage=$CURRENT_STAGE exit=$original_status" >&2
  else
    printf '%s\n' 'FOUNDATION_CONTAINER_TEST_CLEANUP_PASS container=removed image=removed bundle=removed'
  fi

  exit "$original_status"
}

HOST_SHORT=$(hostname --short 2>/dev/null || hostname)
case "${HOST_SHORT,,}" in
  node-01 | vmi3506102)
    printf '%s\n' \
      "FOUNDATION_CONTAINER_TEST_REFUSED host=$HOST_SHORT reason=real_dev_node" >&2
    exit 64
    ;;
esac

if [[ ${FOUNDATION_TEST_PRIVILEGED_CONFIRM:-} != "$PRIVILEGED_CONFIRMATION" ]]; then
  printf '%s\n' \
    'FOUNDATION_CONTAINER_TEST_REFUSED reason=privileged_container_is_root_equivalent' \
    "Run only inside a disposable VM, then set FOUNDATION_TEST_PRIVILEGED_CONFIRM=$PRIVILEGED_CONFIRMATION." >&2
  exit 64
fi

command -v docker >/dev/null 2>&1 || fail 'docker_not_found'
docker version >/dev/null 2>&1 || fail 'docker_daemon_unavailable'
[[ -f "$DOCKERFILE" && ! -L "$DOCKERFILE" ]] || fail 'invalid_fixture_dockerfile'

RUN_TOKEN="$(date -u +%Y%m%d%H%M%S)-$$-${RANDOM}"
IMAGE="cloud-platform-f1-test:$RUN_TOKEN"
CONTAINER="cloud-platform-f1-test-$RUN_TOKEN"
HARNESS_TMP_DIR=$(mktemp -d /tmp/cloud-platform-foundation-test.XXXXXXXX)
trap cleanup EXIT
trap 'exit 130' INT TERM

copy_bundle_file() {
  local relative_path=$1
  local source_path="$REPOSITORY_ROOT/$relative_path"
  local destination_path="$HARNESS_TMP_DIR/repository/$relative_path"

  [[ -f "$source_path" && ! -L "$source_path" ]] ||
    fail "bundle_source_not_regular path=$relative_path"
  install -D -m 0644 -- "$source_path" "$destination_path"
}

CURRENT_STAGE=prepare_allowlisted_bundle
for relative_path in \
  automation/ansible/ansible.cfg \
  automation/ansible/inventory/test-container/group_vars/all.yml \
  automation/ansible/inventory/test-container/hosts.yml \
  automation/ansible/playbooks/controller-preflight.yml \
  automation/ansible/playbooks/foundation.yml \
  automation/ansible/playbooks/rollback-foundation.yml \
  automation/ansible/playbooks/tasks/rollback-foundation-mutate.yml \
  automation/ansible/roles/platform_foundation/defaults/main.yml \
  automation/ansible/roles/platform_foundation/handlers/main.yml \
  automation/ansible/roles/platform_foundation/tasks/main.yml \
  automation/ansible/roles/platform_foundation/tasks/reconcile.yml \
  automation/ansible/roles/platform_foundation/vars/main.yml \
  platform/systemd/cloud-platform.slice \
  platform/systemd/cloud-workloads.slice \
  platform/tmpfiles.d/cloud-platform.conf; do
  copy_bundle_file "$relative_path"
  ((BUNDLE_SOURCE_COUNT += 1))
done
[[ -f "$REPOSITORY_ROOT/requirements-dev.lock" && \
  ! -L "$REPOSITORY_ROOT/requirements-dev.lock" ]] ||
  fail 'bundle_source_not_regular path=requirements-dev.lock'
install -m 0644 -- "$REPOSITORY_ROOT/requirements-dev.lock" \
  "$HARNESS_TMP_DIR/requirements-dev.lock"
((BUNDLE_SOURCE_COUNT += 1))

if find "$HARNESS_TMP_DIR" -type l -print -quit | grep -q .; then
  fail 'allowlisted_bundle_contains_symlink'
fi
if find "$HARNESS_TMP_DIR" \
  \( -name .git -o -name .venv -o -name .ansible -o -name '.env*' \
     -o -name '*.key' -o -name '*.pem' -o -name '*.p12' -o -name '*.pfx' \
     -o -name secrets -o -name credentials \) \
  -print -quit | grep -q .; then
  fail 'allowlisted_bundle_contains_forbidden_path'
fi

printf '%s\n' \
  "FOUNDATION_CONTAINER_PRIVILEGED_GATE_ACCEPTED host=$HOST_SHORT policy=$PRIVILEGED_CONFIRMATION" \
  "FOUNDATION_CONTAINER_BUNDLE_READY source_count=$BUNDLE_SOURCE_COUNT git=absent venv=absent secrets=absent"

CURRENT_STAGE=build_fixture
docker build --tag "$IMAGE" --file "$DOCKERFILE" "$HARNESS_TMP_DIR"

CURRENT_STAGE=start_fixture
docker run \
  --name "$CONTAINER" \
  --privileged \
  --cgroupns private \
  --network none \
  --pids-limit 512 \
  --memory 2g \
  --cpus 2 \
  --detach \
  --stop-timeout 20 \
  --tmpfs /run \
  --tmpfs /run/lock \
  "$IMAGE" >/dev/null

CURRENT_STAGE=wait_for_systemd
systemd_ready=false
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" systemctl is-system-running 2>/dev/null | grep -Eq 'running|degraded'; then
    systemd_ready=true
    break
  fi
  sleep 1
done
if [[ $systemd_ready != true ]]; then
  docker logs "$CONTAINER" >&2 || true
  fail 'systemd_not_ready_after_30_seconds'
fi

run_playbook() {
  docker exec \
    --workdir "$CONTAINER_REPOSITORY_ROOT/automation/ansible" \
    "$CONTAINER" \
    /opt/foundation-test-venv/bin/ansible-playbook \
    --inventory inventory/test-container/hosts.yml \
    "$@"
}

run_playbook_captured() {
  local destination_variable=$1
  local label=$2
  local playbook_output
  local playbook_status
  shift 2

  set +e
  playbook_output=$(run_playbook "$@" 2>&1)
  playbook_status=$?
  set -e

  printf '%s\n' \
    "FOUNDATION_PLAYBOOK_RESULT label=$label exit=$playbook_status" \
    "$playbook_output"
  ((playbook_status == 0)) ||
    fail "playbook_failed label=$label exit=$playbook_status"
  printf -v "$destination_variable" '%s' "$playbook_output"
}

restore_expected_marker() {
  docker exec "$CONTAINER" install \
    --owner root \
    --group root \
    --mode 0600 \
    /run/cloud-platform-foundation.expected \
    "$FOUNDATION_MARKER"
}

foundation_fingerprint() {
  docker exec "$CONTAINER" bash -euo pipefail -c '
    export LC_ALL=C
    getent passwd platform-core || printf "%s\n" "<platform-core-passwd-absent>"
    getent shadow platform-core || printf "%s\n" "<platform-core-shadow-absent>"
    getent group cloud-platform || printf "%s\n" "<cloud-platform-group-absent>"
    for managed_unit in cloud-platform.slice cloud-workloads.slice; do
      systemctl show \
        --property=LoadState,ActiveState,SubState,UnitFileState,TasksCurrent \
        "$managed_unit" || true
    done
    for managed_path in \
      /etc/cloud-platform-foundation.managed \
      /etc/cloud-platform \
      /var/lib/cloud-platform \
      /var/log/cloud-platform \
      /var/cache/cloud-platform \
      /run/cloud-platform \
      /run/lock/cloud-platform-foundation-operation \
      /etc/tmpfiles.d/cloud-platform.conf \
      /etc/systemd/system/cloud-platform.slice \
      /etc/systemd/system/cloud-workloads.slice; do
      if [[ -e "$managed_path" || -L "$managed_path" ]]; then
        find "$managed_path" -xdev \
          -printf "%p|%y|%u|%g|%m|%s|%l\n" | sort
        find "$managed_path" -xdev -type f -exec sha256sum -- {} + | sort
      else
        printf "ABSENT|%s\n" "$managed_path"
      fi
    done
  ' | sha256sum | awk '{print $1}'
}

expect_rollback_refusal_without_change() {
  local scenario=$1
  local before_fingerprint
  local after_fingerprint
  local rollback_failure_output
  local rollback_status

  CURRENT_STAGE="negative_rollback_${scenario}"
  before_fingerprint=$(foundation_fingerprint)

  set +e
  rollback_failure_output=$(run_playbook playbooks/rollback-foundation.yml \
    --extra-vars platform_foundation_rollback_confirm=true --diff 2>&1)
  rollback_status=$?
  set -e

  printf '%s\n' \
    "FOUNDATION_ROLLBACK_EXPECTED_REFUSAL scenario=$scenario exit=$rollback_status" \
    "$rollback_failure_output"
  ((rollback_status != 0)) || fail "rollback_unexpectedly_succeeded scenario=$scenario"

  after_fingerprint=$(foundation_fingerprint)
  [[ $after_fingerprint == "$before_fingerprint" ]] ||
    fail "rollback_refusal_changed_state scenario=$scenario before=$before_fingerprint after=$after_fingerprint"

  printf '%s\n' \
    "FOUNDATION_ROLLBACK_REFUSAL_PASS scenario=$scenario invariant_sha256=$after_fingerprint"
}

CURRENT_STAGE=check_mode
check_mode_before=$(foundation_fingerprint)
run_playbook_captured check_output check_mode \
  playbooks/foundation.yml --check --diff
grep -Eq 'failed=0' <<<"$check_output"
check_mode_after=$(foundation_fingerprint)
[[ $check_mode_after == "$check_mode_before" ]] ||
  fail "check_mode_changed_state before=$check_mode_before after=$check_mode_after"
printf '%s\n' \
  "FOUNDATION_CHECK_MODE_INVARIANCE_PASS sha256=$check_mode_after"

CURRENT_STAGE=partial_marker_check_mode
docker exec "$CONTAINER" sh -eu -c '
  umask 077
  printf "managed_by=cloud-infrastructure\nslice=SLICE-001\nschema=1\nenvironment=test\nnode=node-01" \
    > /etc/cloud-platform-foundation.managed
  chown root:root /etc/cloud-platform-foundation.managed
  chmod 0600 /etc/cloud-platform-foundation.managed
'
partial_check_before=$(foundation_fingerprint)
run_playbook_captured partial_check_output partial_marker_check_mode \
  playbooks/foundation.yml --check --diff
grep -Eq 'failed=0' <<<"$partial_check_output"
partial_check_after=$(foundation_fingerprint)
[[ $partial_check_after == "$partial_check_before" ]] ||
  fail "partial_marker_check_changed_state before=$partial_check_before after=$partial_check_after"
docker exec "$CONTAINER" unlink -- "$FOUNDATION_MARKER"
printf '%s\n' \
  "FOUNDATION_PARTIAL_MARKER_CHECK_PASS sha256=$partial_check_after"

CURRENT_STAGE=first_apply
run_playbook_captured first_output first_apply playbooks/foundation.yml --diff
grep -Eq 'changed=[1-9][0-9]*' <<<"$first_output"

CURRENT_STAGE=idempotence_reconcile
run_playbook_captured second_output idempotence_reconcile \
  playbooks/foundation.yml --diff
grep -Eq 'changed=0' <<<"$second_output"

CURRENT_STAGE=positive_security_assertions
docker exec "$CONTAINER" bash -euo pipefail -c '
  test "$(stat -c %U:%G:%a /etc/cloud-platform-foundation.managed)" = root:root:600
  test "$(stat -c %U:%G:%a /etc/cloud-platform)" = root:cloud-platform:750
  test "$(stat -c %U:%G:%a /var/lib/cloud-platform)" = root:cloud-platform:750
  test "$(stat -c %U:%G:%a /var/log/cloud-platform)" = root:cloud-platform:750
  test "$(stat -c %U:%G:%a /var/cache/cloud-platform)" = root:cloud-platform:750
  test "$(stat -c %U:%G:%a /run/cloud-platform)" = root:cloud-platform:750
  test "$(stat -c %U:%G:%a /run/cloud-platform/credentials)" = root:root:700
  test ! -e /run/lock/cloud-platform-foundation-operation
  test "$(getent passwd platform-core | cut -d: -f7)" = /usr/sbin/nologin
  test "$(getent passwd platform-core | cut -d: -f6)" = /nonexistent
  test "$(passwd -S platform-core | awk "{print \$2}")" = L
  ! id -nG platform-core | grep -Eq "(^| )(sudo|lxd|docker)( |$)"
  ! runuser -u platform-core -- test -w /etc/cloud-platform
  ! runuser -u platform-core -- test -w /var/lib/cloud-platform
  test "$(stat -c %U:%G:%a /etc/tmpfiles.d/cloud-platform.conf)" = root:root:644
  test "$(stat -c %U:%G:%a /etc/systemd/system/cloud-platform.slice)" = root:root:644
  test "$(stat -c %U:%G:%a /etc/systemd/system/cloud-workloads.slice)" = root:root:644
  systemd-analyze verify \
    /etc/systemd/system/cloud-platform.slice \
    /etc/systemd/system/cloud-workloads.slice
'

CURRENT_STAGE=prepare_negative_rollback_tests
docker exec "$CONTAINER" install \
  --owner root \
  --group root \
  --mode 0600 \
  "$FOUNDATION_MARKER" \
  /run/cloud-platform-foundation.expected

docker exec "$CONTAINER" sh -eu -c \
  'printf "%s\n" "managed_by=unexpected" > /etc/cloud-platform-foundation.managed'
expect_rollback_refusal_without_change marker_tampered
restore_expected_marker

docker exec "$CONTAINER" sh -eu -c \
  'printf "%s\n" "rollback-guard" > /var/lib/cloud-platform/rollback-sentinel'
expect_rollback_refusal_without_change persistent_content
docker exec "$CONTAINER" rm -- /var/lib/cloud-platform/rollback-sentinel

docker exec "$CONTAINER" sh -eu -c \
  'printf "%s\n" "rollback-guard" > /run/cloud-platform/credentials/rollback-sentinel'
expect_rollback_refusal_without_change runtime_content
docker exec "$CONTAINER" rm -- /run/cloud-platform/credentials/rollback-sentinel

docker exec "$CONTAINER" rm -- "$FOUNDATION_MARKER"
expect_rollback_refusal_without_change marker_absent
restore_expected_marker
docker exec "$CONTAINER" rm -- /run/cloud-platform-foundation.expected

CURRENT_STAGE=successful_rollback
run_playbook_captured rollback_output successful_rollback \
  playbooks/rollback-foundation.yml \
  --extra-vars platform_foundation_rollback_confirm=true --diff
grep -Eq 'failed=0' <<<"$rollback_output"

CURRENT_STAGE=post_rollback_absence
docker exec "$CONTAINER" sh -eu -c '
  ! getent passwd platform-core
  ! getent group cloud-platform
  test ! -e /etc/cloud-platform-foundation.managed
  test ! -e /etc/cloud-platform
  test ! -e /var/lib/cloud-platform
  test ! -e /var/log/cloud-platform
  test ! -e /var/cache/cloud-platform
  test ! -e /run/cloud-platform
  test ! -e /run/lock/cloud-platform-foundation-operation
  test ! -e /etc/tmpfiles.d/cloud-platform.conf
  test ! -e /etc/systemd/system/cloud-platform.slice
  test ! -e /etc/systemd/system/cloud-workloads.slice
'

CURRENT_STAGE=complete
printf '%s\n' \
  'FOUNDATION_CONTAINER_TEST_PASS check_mode partial_marker_check apply_changed idempotent_changed_0 security_assertions rollback_refusals_4 rollback_clean cleanup_pending'
