#!/usr/bin/env bash
set -Eeuo pipefail

readonly EXPECTED_CONFIRMATION=DISPOSABLE_UBUNTU_24_04_ONLY
REPOSITORY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
readonly REPOSITORY_ROOT
readonly DOCKERFILE="$REPOSITORY_ROOT/tests/fixtures/foundation-systemd/Dockerfile"
readonly CONTAINER_REPOSITORY_ROOT=/workspace/cloud-infrastructure
readonly WORKSPACE_PATH=/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev
readonly STATE_PATH=/var/lib/mcf-control-bridge/state/g2b
readonly GRANT_PATH=/etc/mcf-control-bridge/g2b-grant.json
readonly ENTRYPOINT=/usr/local/libexec/mcf-control-g2b
readonly G2A_ENTRYPOINT=/usr/local/libexec/mcf-control-g2a-protected-read
readonly PILOT_PATH=G2B-PILOT.txt

CURRENT_STAGE=preflight
HARNESS_TMP_DIR=
IMAGE=
CONTAINER=
RUN_TOKEN=
BUNDLE_SOURCE_COUNT=0
UBUNTU_USER_CREATED=false

fail() {
  printf 'G2A_PROTECTED_DISPOSABLE_TEST_FAIL stage=%s reason=%s\n' "$CURRENT_STAGE" "$1" >&2
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
      /tmp/control-bridge-g2a-protected-test.*) rm -rf -- "$HARNESS_TMP_DIR" || cleanup_status=1 ;;
      *) cleanup_status=1 ;;
    esac
  fi
  if ((original_status == 0 && cleanup_status != 0)); then
    original_status=1
  fi
  if ((original_status != 0)); then
    printf 'G2A_PROTECTED_DISPOSABLE_TEST_ABORTED stage=%s exit=%s cleanup=%s\n' \
      "$CURRENT_STAGE" "$original_status" "$cleanup_status" >&2
  fi
  exit "$original_status"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

[[ $# -eq 0 ]] || fail unexpected_arguments
[[ ${G2A_PROTECTED_TEST_PRIVILEGED_CONFIRM:-} == "$EXPECTED_CONFIRMATION" ]] || fail missing_exact_confirmation
[[ ${G2A_PROTECTED_CANDIDATE_SHA:-} =~ ^[0-9a-f]{40}$ ]] || fail invalid_candidate_sha
[[ -f "$DOCKERFILE" && ! -L "$DOCKERFILE" ]] || fail invalid_fixture_dockerfile
command -v docker >/dev/null 2>&1 || fail docker_not_found
docker version >/dev/null 2>&1 || fail docker_daemon_unavailable

HOST_SHORT=$(hostname --short 2>/dev/null || hostname)
case "${HOST_SHORT,,}" in
  node-01 | vmi3506102) fail real_dev_node ;;
esac
if [[ -n ${GITHUB_ACTIONS:-} ]]; then
  [[ ${GITHUB_ACTIONS} == true && ${RUNNER_ENVIRONMENT:-} == github-hosted && ${ImageOS:-} == ubuntu24 ]] ||
    fail not_github_hosted_ubuntu24
fi
if command -v git >/dev/null 2>&1 && git -C "$REPOSITORY_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  [[ $(git -C "$REPOSITORY_ROOT" rev-parse HEAD) == "$G2A_PROTECTED_CANDIDATE_SHA" ]] || fail candidate_sha_mismatch
fi

RUN_TOKEN="$(date -u +%Y%m%d%H%M%S)-$$-${RANDOM}"
IMAGE="control-bridge-g2a-protected-test:$RUN_TOKEN"
CONTAINER="control-bridge-g2a-protected-test-$RUN_TOKEN"
HARNESS_TMP_DIR=$(mktemp -d /tmp/control-bridge-g2a-protected-test.XXXXXXXX)

copy_bundle_file() {
  local relative=$1
  local source="$REPOSITORY_ROOT/$relative"
  local destination="$HARNESS_TMP_DIR/repository/$relative"
  [[ -f "$source" && ! -L "$source" ]] || fail "bundle_source_not_regular:$relative"
  install -D -m 0644 -- "$source" "$destination"
  ((BUNDLE_SOURCE_COUNT += 1))
}

CURRENT_STAGE=prepare_allowlisted_bundle
readonly -a ALLOWLIST=(
  automation/ansible/ansible.cfg
  automation/ansible/inventory/test-container/group_vars/all.yml
  automation/ansible/inventory/test-container/hosts.yml
  automation/ansible/playbooks/controller-preflight.yml
  automation/ansible/playbooks/apply-control-bridge-g2b.yml
  automation/ansible/playbooks/issue-control-bridge-g2b-grant.yml
  automation/ansible/playbooks/apply-control-bridge-g2a-protected-read.yml
  automation/ansible/playbooks/rollback-control-bridge-g2a-protected-read.yml
  automation/ansible/roles/control_bridge_g2b/tasks/main.yml
  automation/ansible/roles/control_bridge_g2b/vars/main.yml
  automation/ansible/roles/control_bridge_g2a_protected_read/tasks/main.yml
  automation/ansible/roles/control_bridge_g2a_protected_read/vars/main.yml
  control_plane/__init__.py
  control_plane/g2a/__init__.py
  control_plane/g2a/errors.py
  control_plane/g2a/protocol.py
  control_plane/g2a/protected_reader.py
  control_plane/g2b/__init__.py
  control_plane/g2b/errors.py
  control_plane/g2b/executor.py
  control_plane/g2b/grant.py
  control_plane/g2b/protocol.py
  control_plane/g2b/secret_policy.py
  control_plane/g2b/state.py
  control_plane/g2b/workspace.py
  platform/control-bridge/mcf-control-g2a-protected-read
  platform/control-bridge/mcf-control-g2b
  platform/sudoers/mcf-control-g2a-protected-read
  platform/sudoers/mcf-control-g2b
  platform/tmpfiles.d/mcf-control-bridge-g2b.conf
  tests/fixtures/g2a/README.md
)
for relative in "${ALLOWLIST[@]}"; do
  copy_bundle_file "$relative"
done
install -m 0644 -- "$REPOSITORY_ROOT/requirements-dev.lock" "$HARNESS_TMP_DIR/requirements-dev.lock"
((BUNDLE_SOURCE_COUNT += 1))
if find "$HARNESS_TMP_DIR" -type l -print -quit | grep -q .; then fail allowlisted_bundle_contains_symlink; fi
if find "$HARNESS_TMP_DIR" \( -name .git -o -name '.env*' -o -name '*.key' -o -name '*.pem' -o -name secrets -o -name credentials \) -print -quit | grep -q .; then
  fail allowlisted_bundle_contains_forbidden_path
fi

CURRENT_STAGE=build_fixture
docker build --quiet --tag "$IMAGE" --file "$DOCKERFILE" "$HARNESS_TMP_DIR" >/dev/null
CURRENT_STAGE=start_fixture
docker run --name "$CONTAINER" --privileged --cgroupns private --network none \
  --pids-limit 512 --memory 2g --cpus 2 --detach --stop-timeout 20 \
  --tmpfs /run --tmpfs /run/lock "$IMAGE" >/dev/null

CURRENT_STAGE=wait_for_systemd
systemd_ready=false
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" systemctl is-system-running 2>/dev/null | grep -Eq 'running|degraded'; then
    systemd_ready=true
    break
  fi
  sleep 1
done
[[ $systemd_ready == true ]] || fail systemd_not_ready

if ! docker exec "$CONTAINER" id -u ubuntu >/dev/null 2>&1; then
  docker exec "$CONTAINER" useradd --create-home --shell /bin/bash ubuntu
  UBUNTU_USER_CREATED=true
fi

# Mirror the real NODE-01 baseline: this generic system parent already exists
# before G2-B bootstrap and must not be mistaken for an orphan G2-B object.
docker exec "$CONTAINER" install -d -o root -g root -m 0755 /usr/local/libexec

run_playbook() {
  docker exec --workdir "$CONTAINER_REPOSITORY_ROOT/automation/ansible" "$CONTAINER" \
    /opt/foundation-test-venv/bin/ansible-playbook --inventory inventory/test-container/hosts.yml "$@"
}

CURRENT_STAGE=apply_g2b
run_playbook playbooks/apply-control-bridge-g2b.yml >/dev/null
run_playbook playbooks/apply-control-bridge-g2b.yml >/dev/null

docker exec "$CONTAINER" getent passwd mcf-workspace | grep -q ':/nonexistent:/usr/sbin/nologin$' || fail service_identity_invalid
[[ $(docker exec "$CONTAINER" id -nG mcf-workspace) == mcf-workspace ]] || fail service_account_privileged_group
[[ $(docker exec "$CONTAINER" stat -c '%U:%G:%a' "$WORKSPACE_PATH") == mcf-workspace:mcf-workspace:700 ]] || fail workspace_metadata_invalid
printf '%s\n' 'G2A_PROTECTED_G2B_BASELINE_PASS'

CURRENT_STAGE=apply_g2a_protected
run_playbook playbooks/apply-control-bridge-g2a-protected-read.yml >/dev/null
printf '%s\n' 'G2A_PROTECTED_APPLY_PASS'

CURRENT_STAGE=idempotence
IDEMPOTENCE_LOG="$HARNESS_TMP_DIR/g2a-protected-idempotence.log"
docker exec --env ANSIBLE_NOCOLOR=1 --workdir "$CONTAINER_REPOSITORY_ROOT/automation/ansible" "$CONTAINER" \
  /opt/foundation-test-venv/bin/ansible-playbook --inventory inventory/test-container/hosts.yml \
  playbooks/apply-control-bridge-g2a-protected-read.yml >"$IDEMPOTENCE_LOG"
RECAP=$(awk '/^node-01[[:space:]]*:/ {line=$0} END {print line}' "$IDEMPOTENCE_LOG")
[[ $RECAP =~ changed=0 ]] || fail idempotence_changed
[[ $RECAP =~ unreachable=0 ]] || fail idempotence_unreachable
[[ $RECAP =~ failed=0 ]] || fail idempotence_failed
printf '%s\n' 'G2A_PROTECTED_IDEMPOTENCE_PASS'
CURRENT_STAGE=direct_read_refusal
if docker exec -u ubuntu "$CONTAINER" test -r "$WORKSPACE_PATH/README.md"; then
  fail direct_read_succeeded
fi
if docker exec -u ubuntu "$CONTAINER" sudo -n true >/dev/null 2>&1; then
  fail generic_sudo_succeeded
fi
if docker exec -u ubuntu "$CONTAINER" sudo -n -u mcf-workspace "$G2A_ENTRYPOINT" extra >/dev/null 2>&1; then
  fail extra_reader_argv_succeeded
fi
printf '%s\n' 'G2A_PROTECTED_DIRECT_READ_REFUSED'

make_g2a_read_request() {
  python3 - "$1" <<'PY'
import json,sys
request_id=sys.argv[1]
value={
  "protocol":"MCF_WORKSPACE_CONTROL_V1",
  "request_id":request_id,
  "project":{"tenant":"leon337","name":"g2a-smoke","environment":"dev"},
  "operation":"workspace.read",
  "arguments":{"path":"G2B-PILOT.txt"},
}
print(json.dumps(value,separators=(",",":")))
PY
}
invoke_g2a_read() {
  local request_id=$1
  make_g2a_read_request "$request_id" | docker exec -i -u ubuntu "$CONTAINER" \
    sudo -n -u mcf-workspace "$G2A_ENTRYPOINT"
}

expect_g2a_read() {
  local value=$1 expected_status=$2 expected_error=$3 expected_sha=${4-any} expected_content=${5-any}
  JSON_VALUE="$value" python3 - "$expected_status" "$expected_error" "$expected_sha" "$expected_content" <<'PY'
import json,os,sys
v=json.loads(os.environ["JSON_VALUE"])
status,error,sha,content=sys.argv[1:]
assert v.get("status") == status, {"status":v.get("status"),"error":v.get("error")}
if error == "null":
    assert v.get("error") is None
else:
    assert v.get("error") == {"code":error}, v.get("error")
if sha != "any": assert v.get("result",{}).get("sha256") == sha
if content != "any": assert v.get("result",{}).get("content") == content
PY
}

CURRENT_STAGE=absent_read
ABSENT_RESULT=$(invoke_g2a_read G2A-PROTECTED-ABSENT-0001)
expect_g2a_read "$ABSENT_RESULT" NOT_FOUND path_not_found
printf '%s\n' 'G2A_PROTECTED_ABSENT_PASS'
CURRENT_STAGE=g2b_grant_issue
EXEC_SHA=$(awk '$1 == "g2b_executor_bundle_sha256:" {print $2}' "$REPOSITORY_ROOT/automation/ansible/roles/control_bridge_g2b/vars/main.yml")
[[ $EXEC_SHA =~ ^[0-9a-f]{64}$ ]] || fail invalid_executor_digest
mapfile -t GRANT_TIMES < <(python3 - <<'PY'
from datetime import datetime, timedelta, timezone
start = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(seconds=5)
print(start.strftime('%Y-%m-%dT%H:%M:%SZ'))
print((start + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ'))
PY
)
GRANT_ID="G2B-G2A-CROSS-DISPOSABLE-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
run_playbook playbooks/issue-control-bridge-g2b-grant.yml \
  -e "g2b_grant_id=$GRANT_ID" \
  -e "g2b_grant_not_before=${GRANT_TIMES[0]}" \
  -e "g2b_grant_not_after=${GRANT_TIMES[1]}" \
  -e "g2b_executor_sha256=$EXEC_SHA" >/dev/null

make_g2b_request() {
  python3 - "$1" "$2" "${3-}" "${4-}" <<'PY'
import json,sys
request_id, operation, content, original = sys.argv[1:]
arguments = {}
if operation == "workspace.write":
    arguments = {"path":"G2B-PILOT.txt","content":content,"precondition":{"state":"ABSENT"}}
elif operation == "rollback":
    arguments = {"original_request_id":original}
value = {
  "transport_principal":{"login":"leon337","actor_id":25374535},
  "request":{
    "protocol":"MCF_WORKSPACE_MUTATION_V1","request_id":request_id,
    "mission_id":"CONTROL-BRIDGE-G2B-PILOT","declared_actor":"MESTRE_MCF",
    "project":{"tenant":"leon337","name":"g2a-smoke","environment":"dev"},
    "operation":operation,"arguments":arguments,
  },
}
print(json.dumps(value,separators=(",",":")))
PY
}

invoke_g2b() {
  local command=$1 request_id=$2 operation=$3 content=${4-} original=${5-}
  local payload
  payload=$(make_g2b_request "$request_id" "$operation" "$content" "$original")
  printf '%s' "$payload" | docker exec -i -u ubuntu "$CONTAINER" \
    sudo -n -u mcf-workspace "$ENTRYPOINT" "$command"
}

expect_g2b_result() {
  local value=$1 expected_status=$2 expected_error=$3
  JSON_VALUE="$value" python3 - "$expected_status" "$expected_error" <<'PY'
import json,os,sys
v=json.loads(os.environ["JSON_VALUE"])
status,error=sys.argv[1:]
assert v.get("status") == status, {"status":v.get("status"),"error":v.get("error")}
if error == "null": assert v.get("error") is None
else: assert v.get("error") == error
PY
}

CURRENT_STAGE=g2b_write
WRITE_ID=G2B-G2A-CROSS-WRITE-0001
CONTENT=$'disposable-g2a-cross-pilot-v1\n'
EXPECTED_HASH=$(printf '%s' "$CONTENT" | sha256sum | awk '{print $1}')
WRITE_RESULT=$(invoke_g2b execute "$WRITE_ID" workspace.write "$CONTENT")
expect_g2b_result "$WRITE_RESULT" PASS null
# Correlate the protected read to the G2-B after.sha256 field.
AFTER_SHA=$(JSON_VALUE="$WRITE_RESULT" python3 - <<'PY'
import json,os
v=json.loads(os.environ["JSON_VALUE"])
print(v["after"]["sha256"])
PY
)
[[ $AFTER_SHA == "$EXPECTED_HASH" ]] || fail g2b_after_sha_mismatch

CURRENT_STAGE=cross_read
CROSS_RESULT=$(invoke_g2a_read G2A-PROTECTED-CROSS-0001)
expect_g2a_read "$CROSS_RESULT" PASS null "$AFTER_SHA" "$CONTENT"
printf '%s\n' 'G2A_PROTECTED_CROSS_READ_PASS'

CURRENT_STAGE=g2b_protocol_rollback
ROLLBACK_RESULT=$(invoke_g2b rollback G2B-G2A-CROSS-ROLLBACK-0001 rollback '' "$WRITE_ID")
expect_g2b_result "$ROLLBACK_RESULT" ROLLED_BACK null
docker exec "$CONTAINER" test ! -e "$WORKSPACE_PATH/$PILOT_PATH" || fail g2b_rollback_left_target
printf '%s\n' 'G2A_PROTECTED_G2B_ROLLBACK_PASS'

CURRENT_STAGE=final_absent_read
FINAL_ABSENT_RESULT=$(invoke_g2a_read G2A-PROTECTED-FINAL-ABSENT-0001)
expect_g2a_read "$FINAL_ABSENT_RESULT" NOT_FOUND path_not_found
printf '%s\n' 'G2A_PROTECTED_FINAL_ABSENT_PASS'

CURRENT_STAGE=g2a_protected_cleanup
ROLLBACK_LOG="$HARNESS_TMP_DIR/rollback-control-bridge-g2a-protected-read.log"
if ! run_playbook playbooks/rollback-control-bridge-g2a-protected-read.yml \
  -e g2a_protected_rollback_confirm=true >"$ROLLBACK_LOG" 2>&1; then
  FAILED_ROLLBACK_TASK=$(awk '
    /^TASK \[/ { current=$0 }
    /^fatal:/ { failed=current }
    END { print failed }
  ' "$ROLLBACK_LOG")
  printf 'G2A_PROTECTED_ROLLBACK_PLAYBOOK_FAIL task=%s\n' \
    "${FAILED_ROLLBACK_TASK:-unknown}" >&2
  fail protected_reader_rollback_failed
fi

for path in \
  /etc/mcf-control-g2a-protected-read.managed \
  /etc/sudoers.d/mcf-control-g2a-protected-read \
  /usr/local/libexec/mcf-control-g2a-protected-read \
  /usr/local/lib/mcf-control-bridge-g2a-protected; do
  docker exec "$CONTAINER" test ! -e "$path" || fail "protected_cleanup_path_survived:$path"
done
docker exec "$CONTAINER" test -e /etc/mcf-control-bridge-g2b.managed || fail g2b_marker_removed
docker exec "$CONTAINER" getent passwd mcf-workspace >/dev/null || fail service_account_removed
docker exec "$CONTAINER" test -d "$WORKSPACE_PATH" || fail workspace_removed
[[ $(docker exec "$CONTAINER" stat -c '%U:%G:%a' "$WORKSPACE_PATH") == mcf-workspace:mcf-workspace:700 ]] || fail workspace_boundary_changed
printf '%s\n' 'G2A_PROTECTED_CLEANUP_PASS'
CURRENT_STAGE=complete
