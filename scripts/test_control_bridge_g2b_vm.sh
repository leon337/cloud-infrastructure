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
readonly PILOT_PATH=G2B-PILOT.txt

CURRENT_STAGE=preflight
HARNESS_TMP_DIR=
IMAGE=
CONTAINER=
RUN_TOKEN=
BUNDLE_SOURCE_COUNT=0
UBUNTU_USER_CREATED=false

fail() {
  printf 'G2B_DISPOSABLE_TEST_FAIL stage=%s reason=%s\n' "$CURRENT_STAGE" "$1" >&2
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
      /tmp/control-bridge-g2b-test.*) rm -rf -- "$HARNESS_TMP_DIR" || cleanup_status=1 ;;
      *) cleanup_status=1 ;;
    esac
  fi
  if ((original_status == 0 && cleanup_status != 0)); then
    original_status=1
  fi
  if ((original_status != 0)); then
    printf 'G2B_DISPOSABLE_TEST_ABORTED stage=%s exit=%s cleanup=%s\n' \
      "$CURRENT_STAGE" "$original_status" "$cleanup_status" >&2
  fi
  exit "$original_status"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

[[ $# -eq 0 ]] || fail unexpected_arguments
[[ ${G2B_TEST_PRIVILEGED_CONFIRM:-} == "$EXPECTED_CONFIRMATION" ]] || fail missing_exact_confirmation
[[ ${G2B_CANDIDATE_SHA:-} =~ ^[0-9a-f]{40}$ ]] || fail invalid_candidate_sha
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
  [[ $(git -C "$REPOSITORY_ROOT" rev-parse HEAD) == "$G2B_CANDIDATE_SHA" ]] || fail candidate_sha_mismatch
fi

RUN_TOKEN="$(date -u +%Y%m%d%H%M%S)-$$-${RANDOM}"
IMAGE="control-bridge-g2b-test:$RUN_TOKEN"
CONTAINER="control-bridge-g2b-test-$RUN_TOKEN"
HARNESS_TMP_DIR=$(mktemp -d /tmp/control-bridge-g2b-test.XXXXXXXX)

copy_bundle_file() {
  local relative=$1
  local source="$REPOSITORY_ROOT/$relative"
  local destination="$HARNESS_TMP_DIR/repository/$relative"
  [[ -f "$source" && ! -L "$source" ]] || fail "bundle_source_not_regular:$relative"
  install -D -m 0644 -- "$source" "$destination"
  ((BUNDLE_SOURCE_COUNT += 1))
}

CURRENT_STAGE=prepare_allowlisted_bundle
for relative in \
  automation/ansible/ansible.cfg \
  automation/ansible/inventory/test-container/group_vars/all.yml \
  automation/ansible/inventory/test-container/hosts.yml \
  automation/ansible/playbooks/controller-preflight.yml \
  automation/ansible/playbooks/apply-control-bridge-g2b.yml \
  automation/ansible/playbooks/issue-control-bridge-g2b-grant.yml \
  automation/ansible/playbooks/rollback-control-bridge-g2b.yml \
  automation/ansible/roles/control_bridge_g2b/tasks/main.yml \
  automation/ansible/roles/control_bridge_g2b/vars/main.yml \
  control_plane/__init__.py \
  control_plane/g2b/__init__.py \
  control_plane/g2b/errors.py \
  control_plane/g2b/executor.py \
  control_plane/g2b/grant.py \
  control_plane/g2b/protocol.py \
  control_plane/g2b/secret_policy.py \
  control_plane/g2b/state.py \
  control_plane/g2b/workspace.py \
  platform/control-bridge/mcf-control-g2b \
  platform/sudoers/mcf-control-g2b \
  platform/tmpfiles.d/mcf-control-bridge-g2b.conf \
  tests/fixtures/g2a/README.md; do
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

run_playbook() {
  docker exec --workdir "$CONTAINER_REPOSITORY_ROOT/automation/ansible" "$CONTAINER" \
    /opt/foundation-test-venv/bin/ansible-playbook --inventory inventory/test-container/hosts.yml "$@"
}

CURRENT_STAGE=apply_g2b
run_playbook playbooks/apply-control-bridge-g2b.yml >/dev/null
run_playbook playbooks/apply-control-bridge-g2b.yml >/dev/null

docker exec "$CONTAINER" getent passwd mcf-workspace | grep -q ':/nonexistent:/usr/sbin/nologin$' || fail service_identity_invalid
[[ $(docker exec "$CONTAINER" id -nG mcf-workspace) == mcf-workspace ]] || fail service_account_privileged_group
[[ $(docker exec "$CONTAINER" stat -c '%U:%G:%a' "$ENTRYPOINT") == root:root:555 ]] || fail entrypoint_metadata_invalid
[[ $(docker exec "$CONTAINER" stat -c '%U:%G:%a' "$WORKSPACE_PATH") == mcf-workspace:mcf-workspace:700 ]] || fail workspace_metadata_invalid
printf '%s\n' 'G2B_DISPOSABLE_IDENTITY_PASS'

CURRENT_STAGE=direct_write_refusal
if docker exec -u ubuntu "$CONTAINER" touch "$WORKSPACE_PATH/$PILOT_PATH" >/dev/null 2>&1; then
  fail direct_transport_write_succeeded
fi
docker exec "$CONTAINER" test ! -e "$WORKSPACE_PATH/$PILOT_PATH" || fail direct_refusal_left_target
printf '%s\n' 'G2B_TRANSPORT_DIRECT_WRITE_REFUSED'

CURRENT_STAGE=grant_issue
EXEC_SHA=$(awk '$1 == "g2b_executor_bundle_sha256:" {print $2}' "$REPOSITORY_ROOT/automation/ansible/roles/control_bridge_g2b/vars/main.yml")
[[ $EXEC_SHA =~ ^[0-9a-f]{64}$ ]] || fail invalid_executor_digest
mapfile -t GRANT_TIMES < <(python3 - <<'PY'
from datetime import datetime, timedelta, timezone
start = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(seconds=5)
print(start.strftime('%Y-%m-%dT%H:%M:%SZ'))
print((start + timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ'))
PY
)
GRANT_ID="G2B-DISPOSABLE-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
run_playbook playbooks/issue-control-bridge-g2b-grant.yml \
  -e "g2b_grant_id=$GRANT_ID" \
  -e "g2b_grant_not_before=${GRANT_TIMES[0]}" \
  -e "g2b_grant_not_after=${GRANT_TIMES[1]}" \
  -e "g2b_executor_sha256=$EXEC_SHA" >/dev/null
[[ $(docker exec "$CONTAINER" stat -c '%U:%G:%a' "$GRANT_PATH") == root:root:644 ]] || fail grant_metadata_invalid
docker exec "$CONTAINER" python3 -c 'import json,datetime,pathlib; p=pathlib.Path("/etc/mcf-control-bridge/g2b-grant.json"); v=json.loads(p.read_text()); a=datetime.datetime.fromisoformat(v["not_before"].replace("Z","+00:00")); b=datetime.datetime.fromisoformat(v["not_after"].replace("Z","+00:00")); assert (b-a).total_seconds()==86400 and v["enabled"] is True'
printf '%s\n' 'G2B_GRANT_24H_PASS'

make_request() {
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

invoke() {
  local command=$1 request_id=$2 operation=$3 content=${4-} original=${5-}
  local payload
  payload=$(make_request "$request_id" "$operation" "$content" "$original")
  printf '%s' "$payload" | docker exec -i -u ubuntu "$CONTAINER" \
    sudo -n -u mcf-workspace "$ENTRYPOINT" "$command"
}

expect_result() {
  local value=$1 expected_status=$2 expected_error=$3 expected_replayed=${4-any} expected_sha=${5-any}
  JSON_VALUE="$value" python3 - "$expected_status" "$expected_error" "$expected_replayed" "$expected_sha" <<'PY'
import json,os,sys
v=json.loads(os.environ["JSON_VALUE"])
status,error,replayed,sha=sys.argv[1:]
observed = {"status": v.get("status"), "error": v.get("error")}
assert v["status"] == status, observed
if error == "null": assert v.get("error") is None, observed
else: assert v.get("error") == error, observed
if replayed != "any": assert v.get("replayed") is (replayed == "true"), v.get("replayed")
if sha != "any": assert v.get("after",{}).get("sha256") == sha, v.get("after")
PY
}

CURRENT_STAGE='write'
WRITE_ID=G2B-DISPOSABLE-WRITE-0001
CONTENT=$'disposable-pilot-v1\n'
EXPECTED_HASH=$(printf '%s' "$CONTENT" | sha256sum | awk '{print $1}')
WRITE_RESULT=$(invoke execute "$WRITE_ID" workspace.write "$CONTENT")
expect_result "$WRITE_RESULT" PASS null false "$EXPECTED_HASH"
[[ $(docker exec "$CONTAINER" sha256sum "$WORKSPACE_PATH/$PILOT_PATH" | awk '{print $1}') == "$EXPECTED_HASH" ]] || fail write_hash_mismatch
printf '%s\n' 'G2B_WRITE_PASS'

CURRENT_STAGE=replay
BEFORE_STAT=$(docker exec "$CONTAINER" stat -c '%i:%Y:%s' "$WORKSPACE_PATH/$PILOT_PATH")
REPLAY_RESULT=$(invoke execute "$WRITE_ID" workspace.write "$CONTENT")
AFTER_STAT=$(docker exec "$CONTAINER" stat -c '%i:%Y:%s' "$WORKSPACE_PATH/$PILOT_PATH")
expect_result "$REPLAY_RESULT" PASS null true "$EXPECTED_HASH"
[[ $BEFORE_STAT == "$AFTER_STAT" ]] || fail replay_touched_target
printf '%s\n' 'G2B_REPLAY_PASS'

CURRENT_STAGE=request_id_conflict
CONFLICT_RESULT=$(invoke execute "$WRITE_ID" workspace.write $'changed-disposable-pilot\n')
expect_result "$CONFLICT_RESULT" CONFLICT request_id_conflict false any
printf '%s\n' 'G2B_REQUEST_ID_CONFLICT_PASS'

CURRENT_STAGE=concurrency
CONCURRENCY_RESULT=$(invoke execute G2B-DISPOSABLE-WRITE-0002 workspace.write $'second-disposable-pilot\n')
expect_result "$CONCURRENCY_RESULT" CONFLICT active_mutation_exists false any
printf '%s\n' 'G2B_CONCURRENCY_PASS'

CURRENT_STAGE=audit
[[ $(docker exec "$CONTAINER" stat -c '%U:%G:%a' "$STATE_PATH/audit.jsonl") == mcf-workspace:mcf-workspace:600 ]] || fail audit_metadata_invalid
docker exec "$CONTAINER" grep -Fq "$WRITE_ID" "$STATE_PATH/audit.jsonl" || fail audit_request_missing
if docker exec "$CONTAINER" grep -Fq '"content"' "$STATE_PATH/audit.jsonl"; then fail audit_contains_content; fi
RECEIPT_COUNT=$(docker exec "$CONTAINER" find "$STATE_PATH/receipts" -maxdepth 1 -type f | wc -l)
[[ $RECEIPT_COUNT -ge 1 ]] || fail receipt_missing
printf '%s\n' 'G2B_AUDIT_PASS'

CURRENT_STAGE=rollback
ROLLBACK_RESULT=$(invoke rollback G2B-DISPOSABLE-ROLLBACK-0001 rollback '' "$WRITE_ID")
expect_result "$ROLLBACK_RESULT" ROLLED_BACK null false any
docker exec "$CONTAINER" test ! -e "$WORKSPACE_PATH/$PILOT_PATH" || fail rollback_left_target
printf '%s\n' 'G2B_ROLLBACK_PASS'

CURRENT_STAGE=final_state
STATUS_RESULT=$(invoke status G2B-DISPOSABLE-STATUS-0001 status)
expect_result "$STATUS_RESULT" PASS null false any
docker exec "$CONTAINER" test ! -e "$WORKSPACE_PATH/$PILOT_PATH" || fail final_target_present
printf '%s\n' 'G2B_FINAL_STATE_PASS'

CURRENT_STAGE=revoke
REVOKE_RESULT=$(invoke revoke G2B-DISPOSABLE-REVOKE-0001 revoke)
expect_result "$REVOKE_RESULT" REVOKED null false any
printf '%s\n' 'G2B_REVOKE_PASS'

CURRENT_STAGE=post_revoke
POST_REVOKE_RESULT=$(invoke execute G2B-DISPOSABLE-WRITE-POST-REVOKE workspace.write $'must-not-write\n')
expect_result "$POST_REVOKE_RESULT" REFUSED grant_revoked false any
docker exec "$CONTAINER" test ! -e "$WORKSPACE_PATH/$PILOT_PATH" || fail post_revoke_created_target
printf '%s\n' 'G2B_POST_REVOKE_REFUSAL_PASS'

CURRENT_STAGE=bounded_cleanup
ROLLBACK_LOG="$HARNESS_TMP_DIR/rollback-control-bridge-g2b.log"
if ! run_playbook playbooks/rollback-control-bridge-g2b.yml \
  -e g2b_rollback_confirm=true >"$ROLLBACK_LOG" 2>&1; then
  FAILED_ROLLBACK_TASK=$(awk '
    /^TASK \[/ { current=$0 }
    /^fatal:/ { failed=current }
    END { print failed }
  ' "$ROLLBACK_LOG")
  printf 'G2B_ROLLBACK_PLAYBOOK_FAIL task=%s\n' \
    "${FAILED_ROLLBACK_TASK:-unknown}" >&2
  fail rollback_playbook_failed
fi
if [[ $UBUNTU_USER_CREATED == true ]]; then
  docker exec "$CONTAINER" userdel --remove ubuntu >/dev/null 2>&1 || true
fi
for path in \
  /etc/mcf-control-bridge-g2b.managed \
  /etc/mcf-control-bridge/g2b-grant.json \
  /usr/local/libexec/mcf-control-g2b \
  /etc/sudoers.d/mcf-control-g2b \
  /etc/tmpfiles.d/mcf-control-bridge-g2b.conf \
  /var/lib/mcf-control-bridge/state/g2b \
  /var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev; do
  docker exec "$CONTAINER" test ! -e "$path" || fail "cleanup_path_survived:$path"
done
if docker exec "$CONTAINER" getent passwd mcf-workspace >/dev/null 2>&1; then fail service_account_survived_cleanup; fi
printf '%s\n' 'G2B_BOUNDED_CLEANUP_PASS'
CURRENT_STAGE=complete
