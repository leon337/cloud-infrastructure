#!/usr/bin/env bash
set -Eeuo pipefail

readonly MISSION_ID=CODEX-EXECUTION-MISSION-001
readonly EXPECTED_HOST=vmi3506102
readonly EXPECTED_MACHINE_ID_SHA256=27cff9587c434cf9024bd88468a8997778a64ce9ca5c3dc8dbcb68e0aee8f107
readonly EXPECTED_SUDO_USER=ubuntu
readonly EXPECTED_BRANCH=codex/mission-001-f1-2c-network-enforcement
readonly SOURCE_BUNDLE=/tmp/codex-mission-001.bundle
readonly SOURCE_SIGNATURE=/tmp/codex-mission-001.bundle.sig
readonly SIGNING_NAMESPACE=codex-mission-001
readonly SIGNING_IDENTITY=mission-001-controller
readonly SIGNING_PUBLIC_KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGYR3gCchzYiIl5wVyx8NIg+vxcC0DtSG/NNkSfHn6pF'
readonly RUNNER_PATH=/usr/local/sbin/codex-mission-001-runner
readonly REVOKE_PATH=/usr/local/libexec/codex-mission-001-revoke
readonly SUDOERS_PATH=/etc/sudoers.d/91-codex-mission-001-temporary
readonly SERVICE_PATH=/etc/systemd/system/codex-mission-001-revoke.service
readonly TIMER_PATH=/etc/systemd/system/codex-mission-001-revoke.timer
readonly STATE_ROOT=/var/lib/codex-mission-001
readonly REPO_ROOT=/opt/codex-mission-001/repository
readonly LOG_ROOT=/var/log/codex-mission-001
readonly MARKER=/etc/codex-mission-001-autonomous-runner.managed

refuse() {
  printf 'BOOTSTRAP_REFUSED reason=%s\n' "$1" >&2
  exit 2
}

[[ $EUID -eq 0 ]] || refuse must_run_as_root_via_sudo
[[ ${SUDO_USER:-} == "$EXPECTED_SUDO_USER" ]] || refuse unexpected_sudo_user
[[ $(hostname) == "$EXPECTED_HOST" ]] || refuse unexpected_hostname
machine_id_sha256=$(tr -d '\n' </etc/machine-id | sha256sum | awk '{print $1}')
[[ $machine_id_sha256 == "$EXPECTED_MACHINE_ID_SHA256" ]] || refuse unexpected_machine_id
[[ -f $SOURCE_BUNDLE && ! -L $SOURCE_BUNDLE ]] || refuse source_bundle_missing_or_not_regular
[[ -f $SOURCE_SIGNATURE && ! -L $SOURCE_SIGNATURE ]] ||
  refuse source_signature_missing_or_not_regular
[[ $(stat -c '%U:%G:%a:%h' "$SOURCE_BUNDLE") == ubuntu:ubuntu:600:1 ]] ||
  refuse source_bundle_owner_mode_or_links_invalid
[[ $(stat -c '%U:%G:%a:%h' "$SOURCE_SIGNATURE") == ubuntu:ubuntu:600:1 ]] ||
  refuse source_signature_owner_mode_or_links_invalid
[[ $(stat -c '%s' "$SOURCE_BUNDLE") -le 67108864 ]] || refuse source_bundle_too_large
[[ $(stat -c '%s' "$SOURCE_SIGNATURE") -le 16384 ]] || refuse source_signature_too_large
command -v git >/dev/null || refuse git_missing
command -v ssh-keygen >/dev/null || refuse ssh_keygen_missing
command -v visudo >/dev/null || refuse visudo_missing
command -v systemctl >/dev/null || refuse systemctl_missing
for command_name in flock logger runuser iptables ip ss sysctl stat; do
  command -v "$command_name" >/dev/null || refuse "required_command_missing:$command_name"
done

libexec_created=false
if [[ -e /usr/local/libexec || -L /usr/local/libexec ]]; then
  [[ -d /usr/local/libexec && ! -L /usr/local/libexec ]] || refuse unsafe_libexec_parent
  [[ $(stat -c '%U:%G:%a' /usr/local/libexec) == root:root:755 ]] ||
    refuse unsafe_libexec_parent_metadata
else
  libexec_created=true
fi

for path in \
  "$RUNNER_PATH" "$REVOKE_PATH" "$SUDOERS_PATH" "$SERVICE_PATH" \
  "$TIMER_PATH" "$STATE_ROOT" /opt/codex-mission-001 "$LOG_ROOT" "$MARKER"; do
  [[ ! -e $path && ! -L $path ]] || refuse "preexisting_object:$path"
done

workdir=$(mktemp -d /run/codex-mission-001-bootstrap.XXXXXX)
bootstrap_complete=false
cleanup() {
  exit_code=$?
  rm -rf --one-file-system "$workdir"
  if [[ $bootstrap_complete != true ]]; then
    systemctl disable --now codex-mission-001-revoke.timer >/dev/null 2>&1 || true
    rm -f -- "$SUDOERS_PATH" "$RUNNER_PATH" "$REVOKE_PATH" "$SERVICE_PATH" \
      "$TIMER_PATH" "$MARKER"
    rm -rf --one-file-system "$STATE_ROOT" "$LOG_ROOT" /opt/codex-mission-001
    if [[ $libexec_created == true ]]; then rmdir /usr/local/libexec 2>/dev/null || true; fi
    systemctl daemon-reload >/dev/null 2>&1 || true
  fi
  exit "$exit_code"
}
trap cleanup EXIT

printf '%s %s\n' "$SIGNING_IDENTITY" "$SIGNING_PUBLIC_KEY" >"$workdir/allowed_signers"
chmod 0600 "$workdir/allowed_signers"
ssh-keygen -Y verify -f "$workdir/allowed_signers" -I "$SIGNING_IDENTITY" \
  -n "$SIGNING_NAMESPACE" -s "$SOURCE_SIGNATURE" <"$SOURCE_BUNDLE" >/dev/null 2>&1 ||
  refuse invalid_bundle_signature
git init --bare --quiet "$workdir/verify.git" || refuse bundle_verifier_init_failed
git -C "$workdir/verify.git" bundle verify "$SOURCE_BUNDLE" >/dev/null 2>&1 ||
  refuse invalid_git_bundle
git clone --quiet --branch "$EXPECTED_BRANCH" --single-branch \
  "$SOURCE_BUNDLE" "$workdir/repository" || refuse branch_missing_from_bundle
git -C "$workdir/repository" diff --quiet || refuse bundle_worktree_dirty
git -C "$workdir/repository" diff --cached --quiet || refuse bundle_index_dirty
[[ -f $workdir/repository/docs/CODEX-EXECUTION-MISSION-001.md ]] || refuse mission_missing
[[ -f $workdir/repository/state/current.yaml ]] || refuse current_state_missing
grep -Eq '^[[:space:]]*production_promotion_authorized:[[:space:]]+false$' \
  "$workdir/repository/state/current.yaml" ||
  refuse production_guard_missing
grep -Eq '^[[:space:]]*production_promotion:[[:space:]]+NOT_AUTHORIZED_HUMAN_GATE_REQUIRED$' \
  "$workdir/repository/state/current.yaml" || refuse production_human_gate_missing
! grep -Eq '^[[:space:]]*production_promotion_authorized:[[:space:]]+true$' \
  "$workdir/repository/state/current.yaml" || refuse production_guard_true
grep -q 'DEFERRED_BY_HUMAN_DECISION' "$workdir/repository/state/current.yaml" ||
  refuse credential_rotation_not_deferred
initial_sha=$(git -C "$workdir/repository" rev-parse HEAD)

install -d -o root -g root -m 0755 /usr/local/libexec
install -d -o root -g root -m 0755 /opt/codex-mission-001
install -d -o root -g ubuntu -m 0710 "$STATE_ROOT"
install -d -o root -g root -m 0750 "$LOG_ROOT"
install -d -o ubuntu -g ubuntu -m 0700 "$STATE_ROOT/inbox"
mv "$workdir/repository" "$REPO_ROOT"
chown -R root:root "$REPO_ROOT"
chmod -R a+rX,go-w "$REPO_ROOT"

expires_epoch=$(( $(date -u +%s) + 43200 ))
expires_calendar=$(date -u -d "@$expires_epoch" '+%Y-%m-%d %H:%M:%S UTC')
printf '%s\n' "$expires_epoch" >"$STATE_ROOT/expires_epoch"
printf '%s\n' "$EXPECTED_BRANCH" >"$STATE_ROOT/expected_branch"
printf '%s\n' "$initial_sha" >"$STATE_ROOT/active_sha"
install -o root -g root -m 0600 "$workdir/allowed_signers" "$STATE_ROOT/allowed_signers"
chown root:root "$STATE_ROOT/expires_epoch" "$STATE_ROOT/expected_branch" "$STATE_ROOT/active_sha"
chmod 0600 "$STATE_ROOT/expires_epoch" "$STATE_ROOT/expected_branch" "$STATE_ROOT/active_sha"
touch "$LOG_ROOT/runner.log"
chown root:adm "$LOG_ROOT/runner.log"
chmod 0640 "$LOG_ROOT/runner.log"

cat >"$workdir/runner" <<'RUNNER'
#!/usr/bin/env bash
set -Eeuo pipefail

readonly STATE_ROOT=/var/lib/codex-mission-001
readonly REPO_ROOT=/opt/codex-mission-001/repository
readonly LOG_FILE=/var/log/codex-mission-001/runner.log
readonly LOCK_FILE=/run/lock/codex-mission-001-runner.lock
readonly EXPECTED_HOST=vmi3506102
readonly EXPECTED_MACHINE_ID_SHA256=27cff9587c434cf9024bd88468a8997778a64ce9ca5c3dc8dbcb68e0aee8f107
readonly EXPECTED_BRANCH=codex/mission-001-f1-2c-network-enforcement
readonly INBOX_BUNDLE=/var/lib/codex-mission-001/inbox/repository.bundle
readonly INBOX_SIGNATURE=/var/lib/codex-mission-001/inbox/repository.bundle.sig
readonly ALLOWED_SIGNERS=/var/lib/codex-mission-001/allowed_signers
readonly SIGNING_NAMESPACE=codex-mission-001
readonly SIGNING_IDENTITY=mission-001-controller
readonly SUDOERS_PATH=/etc/sudoers.d/91-codex-mission-001-temporary
readonly ALLOWED_OPERATIONS='check apply test reconcile rollback status'

export PATH=/usr/sbin:/usr/bin:/sbin:/bin
export GIT_OPTIONAL_LOCKS=0
unset BASH_ENV CDPATH ENV GIT_CONFIG_COUNT GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM \
  GIT_DIR GIT_WORK_TREE LD_LIBRARY_PATH LD_PRELOAD PYTHONPATH
umask 077

operation=${1:-}
[[ $# -eq 1 ]] || { printf 'RUNNER_REFUSED reason=exactly_one_operation_required\n' >&2; exit 64; }
case " $ALLOWED_OPERATIONS " in
  *" $operation "*) ;;
  *) printf 'RUNNER_REFUSED reason=operation_not_allowlisted\n' >&2; exit 64 ;;
esac

exec 9>"$LOCK_FILE"
flock -n 9 || { printf 'RUNNER_REFUSED reason=concurrent_operation\n' >&2; exit 75; }

sha=UNAVAILABLE
if [[ -d $REPO_ROOT/.git ]]; then
  sha=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || printf UNAVAILABLE)
fi
started_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
result=FAILED_BEFORE_DISPATCH
finish() {
  exit_code=$?
  if [[ $exit_code -eq 0 ]]; then result=PASS; else result="FAIL_EXIT_${exit_code}"; fi
  finished_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
  printf 'timestamp=%s operation=%s git_sha=%s result=%s\n' \
    "$finished_at" "$operation" "$sha" "$result" >>"$LOG_FILE"
  logger -t codex-mission-001 \
    "timestamp=$finished_at operation=$operation git_sha=$sha result=$result"
}
trap finish EXIT

[[ $EUID -eq 0 ]] || { printf 'RUNNER_REFUSED reason=root_required\n' >&2; exit 77; }
[[ $(hostname) == "$EXPECTED_HOST" ]] || { printf 'RUNNER_REFUSED reason=wrong_host\n' >&2; exit 77; }
machine_id_sha256=$(tr -d '\n' </etc/machine-id | sha256sum | awk '{print $1}')
[[ $machine_id_sha256 == "$EXPECTED_MACHINE_ID_SHA256" ]] || {
  printf 'RUNNER_REFUSED reason=wrong_machine_id\n' >&2
  exit 77
}
expires_epoch=$(<"$STATE_ROOT/expires_epoch")
[[ $expires_epoch =~ ^[0-9]+$ ]] || { printf 'RUNNER_REFUSED reason=invalid_expiry\n' >&2; exit 78; }
if (( $(date -u +%s) >= expires_epoch )); then
  rm -f -- "$SUDOERS_PATH"
  visudo -cf /etc/sudoers >/dev/null || true
  printf 'RUNNER_REFUSED reason=authorization_expired_and_revoked\n' >&2
  exit 79
fi

require_repository_guards() {
  [[ -d $REPO_ROOT/.git && ! -L $REPO_ROOT ]] || return 1
  [[ $(stat -c '%U:%G' "$REPO_ROOT") == root:root ]] || return 1
  [[ $(git -C "$REPO_ROOT" branch --show-current) == "$EXPECTED_BRANCH" ]] || return 1
  git -C "$REPO_ROOT" diff --quiet || return 1
  git -C "$REPO_ROOT" diff --cached --quiet || return 1
  [[ -f $REPO_ROOT/docs/CODEX-EXECUTION-MISSION-001.md ]] || return 1
  grep -q 'DEFERRED_BY_HUMAN_DECISION' "$REPO_ROOT/state/current.yaml" || return 1
  grep -Eq '^[[:space:]]*production_promotion_authorized:[[:space:]]+false$' \
    "$REPO_ROOT/state/current.yaml" || return 1
  grep -Eq '^[[:space:]]*production_promotion:[[:space:]]+NOT_AUTHORIZED_HUMAN_GATE_REQUIRED$' \
    "$REPO_ROOT/state/current.yaml" || return 1
  ! grep -Eq '^[[:space:]]*production_promotion_authorized:[[:space:]]+true$' \
    "$REPO_ROOT/state/current.yaml" || return 1
}

status_operation() {
  require_repository_guards || { printf 'STATUS_FAIL repository_guard\n' >&2; return 1; }
  printf 'MISSION_RUNNER_STATUS=ACTIVE\n'
  printf 'MISSION_ID=CODEX-EXECUTION-MISSION-001\n'
  printf 'GIT_SHA=%s\n' "$sha"
  printf 'EXPIRES_EPOCH=%s\n' "$expires_epoch"
  systemctl is-active ssh ufw fail2ban xrdp xrdp-sesman docker containerd
  if systemctl is-active --quiet snap.lxd.daemon.service; then return 1; fi
  if systemctl is-active --quiet snap.lxd.daemon.unix.socket; then return 1; fi
  [[ $(stat -c '%U:%G:%a' /var/run/docker.sock) == root:root:600 ]]
}

check_operation() {
  status_operation
  ipv4_forward=$(sysctl -n net.ipv4.ip_forward)
  if [[ $ipv4_forward != 0 ]]; then
    marker=/etc/cloud-platform-network-enforcement.managed
    [[ -f $marker && ! -L $marker ]]
    [[ $(stat -c '%U:%G:%a:%h' "$marker") == root:root:600:1 ]]
    iptables -C DOCKER-USER -j CLOUD-PLATFORM-FWD
  fi
  [[ $(sysctl -n net.ipv6.conf.all.forwarding) == 0 ]]
  if ip -o link show | awk -F': ' '{print $2}' |
      grep -Eq '^(docker0|br-|cp[0-9a-f]{8})(@|$)'; then return 1; fi
  if ss -Hlnptu | grep -Eq '(^|:)(2375|2376)([[:space:]]|$)'; then return 1; fi
  printf 'MISSION_RUNNER_CHECK=PASS\n'
}

test_operation() (
  require_repository_guards || return 1
  local test_root test_path
  test_root=$(mktemp -d /var/tmp/codex-mission-001-test.XXXXXX)
  trap 'rm -rf --one-file-system "$test_root"' EXIT
  cp -a -- "$REPO_ROOT/." "$test_root/"
  chown -R ubuntu:ubuntu "$test_root"
  chmod -R u+rwX,go-rwx "$test_root"
  test_path="$test_root/scripts/test.sh"
  [[ -f $test_path && ! -L $test_path ]] || return 1
  runuser -u ubuntu -- env \
    PATH=/home/ubuntu/cloud-infrastructure/.venv/bin:/usr/bin:/bin \
    HOME=/home/ubuntu \
    GIT_CONFIG_COUNT=1 \
    GIT_CONFIG_KEY_0=safe.directory \
    GIT_CONFIG_VALUE_0="$test_root" \
    "$test_path"
)

reconcile_operation() (
  [[ -f $INBOX_BUNDLE && ! -L $INBOX_BUNDLE && \
     -f $INBOX_SIGNATURE && ! -L $INBOX_SIGNATURE ]] || {
    printf 'RECONCILE_REFUSED reason=fixed_signed_inbox_bundle_missing\n' >&2
    return 1
  }
  [[ $(stat -c '%U:%G:%a:%h' "$INBOX_BUNDLE") == ubuntu:ubuntu:600:1 ]] || return 1
  [[ $(stat -c '%U:%G:%a:%h' "$INBOX_SIGNATURE") == ubuntu:ubuntu:600:1 ]] || return 1
  [[ $(stat -c '%s' "$INBOX_BUNDLE") -le 67108864 ]] || return 1
  [[ $(stat -c '%s' "$INBOX_SIGNATURE") -le 16384 ]] || return 1
  local staging previous candidate_sha
  staging=$(mktemp -d /opt/codex-mission-001/reconcile.XXXXXX)
  previous=/opt/codex-mission-001/repository.previous
  trap 'rm -rf --one-file-system "$staging"' EXIT
  [[ -f $ALLOWED_SIGNERS && ! -L $ALLOWED_SIGNERS ]]
  [[ $(stat -c '%U:%G:%a:%h' "$ALLOWED_SIGNERS") == root:root:600:1 ]]
  ssh-keygen -Y verify -f "$ALLOWED_SIGNERS" -I "$SIGNING_IDENTITY" \
    -n "$SIGNING_NAMESPACE" -s "$INBOX_SIGNATURE" <"$INBOX_BUNDLE" >/dev/null 2>&1 ||
    return 1
  git init --bare --quiet "$staging/verify.git" || return 1
  git -C "$staging/verify.git" bundle verify "$INBOX_BUNDLE" >/dev/null 2>&1 || return 1
  git clone --quiet --branch "$EXPECTED_BRANCH" --single-branch \
    "$INBOX_BUNDLE" "$staging/repository" || return 1
  candidate_sha=$(git -C "$staging/repository" rev-parse HEAD)
  git -C "$staging/repository" diff --quiet || return 1
  git -C "$staging/repository" diff --cached --quiet || return 1
  [[ -f $staging/repository/docs/CODEX-EXECUTION-MISSION-001.md ]] || return 1
  grep -q 'DEFERRED_BY_HUMAN_DECISION' "$staging/repository/state/current.yaml" || return 1
  grep -Eq '^[[:space:]]*production_promotion_authorized:[[:space:]]+false$' \
    "$staging/repository/state/current.yaml" || return 1
  grep -Eq '^[[:space:]]*production_promotion:[[:space:]]+NOT_AUTHORIZED_HUMAN_GATE_REQUIRED$' \
    "$staging/repository/state/current.yaml" || return 1
  ! grep -Eq '^[[:space:]]*production_promotion_authorized:[[:space:]]+true$' \
    "$staging/repository/state/current.yaml" || return 1
  chown -R root:root "$staging/repository"
  chmod -R a+rX,go-w "$staging/repository"
  [[ ! -L $previous ]] || return 1
  if [[ -e $previous ]]; then
    [[ -d $previous && $(stat -c '%U:%G' "$previous") == root:root ]] || return 1
    rm -rf --one-file-system "$previous"
  fi
  mv "$REPO_ROOT" "$previous"
  mv "$staging/repository" "$REPO_ROOT"
  printf '%s\n' "$candidate_sha" >"$STATE_ROOT/active_sha"
  chown root:root "$STATE_ROOT/active_sha"
  chmod 0600 "$STATE_ROOT/active_sha"
  rm -f -- "$INBOX_BUNDLE" "$INBOX_SIGNATURE"
  sha=$candidate_sha
  printf 'MISSION_RUNNER_RECONCILE=PASS GIT_SHA=%s\n' "$candidate_sha"
)

privileged_operation() {
  require_repository_guards || return 1
  local entrypoint="$REPO_ROOT/automation/mission-001/operations/$operation"
  [[ -f $entrypoint && ! -L $entrypoint && -x $entrypoint ]] || {
    printf 'RUNNER_REFUSED reason=reviewed_%s_entrypoint_not_installed\n' "$operation" >&2
    return 69
  }
  [[ $(stat -c '%U:%G:%a:%h' "$entrypoint") == root:root:755:1 ]] || return 1
  env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin HOME=/root \
    MISSION_ID=CODEX-EXECUTION-MISSION-001 \
    MISSION_REPOSITORY="$REPO_ROOT" \
    MISSION_GIT_SHA="$sha" \
    "$entrypoint"
}

printf 'MISSION_RUNNER_START timestamp=%s operation=%s git_sha=%s\n' \
  "$started_at" "$operation" "$sha"
case "$operation" in
  status) status_operation ;;
  check) check_operation ;;
  test) test_operation ;;
  reconcile) reconcile_operation ;;
  apply|rollback) privileged_operation ;;
esac
RUNNER

cat >"$workdir/revoke" <<'REVOKE'
#!/usr/bin/env bash
set -Eeuo pipefail
readonly SUDOERS_PATH=/etc/sudoers.d/91-codex-mission-001-temporary
readonly LOG_FILE=/var/log/codex-mission-001/runner.log
[[ $EUID -eq 0 ]] || { printf 'REVOKE_REFUSED reason=root_required\n' >&2; exit 77; }
timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
rm -f -- "$SUDOERS_PATH"
if ! visudo -cf /etc/sudoers >/dev/null; then
  printf 'timestamp=%s operation=automatic-revoke git_sha=NOT_APPLICABLE result=FAIL_SUDOERS\n' \
    "$timestamp" >>"$LOG_FILE"
  exit 1
fi
printf 'timestamp=%s operation=automatic-revoke git_sha=NOT_APPLICABLE result=PASS\n' \
  "$timestamp" >>"$LOG_FILE"
logger -t codex-mission-001 \
  "timestamp=$timestamp operation=automatic-revoke git_sha=NOT_APPLICABLE result=PASS"
REVOKE

cat >"$workdir/sudoers" <<'SUDOERS'
Cmnd_Alias CODEX_MISSION_001_TEMP = \
    /usr/local/sbin/codex-mission-001-runner check, \
    /usr/local/sbin/codex-mission-001-runner apply, \
    /usr/local/sbin/codex-mission-001-runner test, \
    /usr/local/sbin/codex-mission-001-runner reconcile, \
    /usr/local/sbin/codex-mission-001-runner rollback, \
    /usr/local/sbin/codex-mission-001-runner status
ubuntu ALL=(root) NOPASSWD: NOSETENV: CODEX_MISSION_001_TEMP
SUDOERS

cat >"$workdir/service" <<EOF
[Unit]
Description=Revoke temporary Codex Mission 001 sudo capability
After=local-fs.target

[Service]
Type=oneshot
ExecStart=$REVOKE_PATH
EOF

cat >"$workdir/timer" <<EOF
[Unit]
Description=Expire temporary Codex Mission 001 sudo capability after 12 hours

[Timer]
OnCalendar=$expires_calendar
Persistent=true
AccuracySec=1s
Unit=codex-mission-001-revoke.service

[Install]
WantedBy=timers.target
EOF

cat >"$workdir/marker" <<EOF
mission=$MISSION_ID
installed_at_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
expires_epoch=$expires_epoch
initial_git_sha=$initial_sha
production=false
credential_rotation=DEFERRED_BY_HUMAN_DECISION
EOF

chmod 0755 "$workdir/runner" "$workdir/revoke"
chmod 0440 "$workdir/sudoers"
chmod 0644 "$workdir/service" "$workdir/timer"
chmod 0600 "$workdir/marker"
visudo -cf "$workdir/sudoers" >/dev/null || refuse generated_sudoers_invalid

install -o root -g root -m 0755 "$workdir/runner" "$RUNNER_PATH"
install -o root -g root -m 0755 "$workdir/revoke" "$REVOKE_PATH"
install -o root -g root -m 0644 "$workdir/service" "$SERVICE_PATH"
install -o root -g root -m 0644 "$workdir/timer" "$TIMER_PATH"
install -o root -g root -m 0600 "$workdir/marker" "$MARKER"
install -o root -g root -m 0440 "$workdir/sudoers" "$SUDOERS_PATH"

if ! visudo -cf /etc/sudoers >/dev/null; then
  rm -f -- "$SUDOERS_PATH"
  refuse installed_sudoers_invalid_and_removed
fi

systemctl daemon-reload
systemctl enable --now codex-mission-001-revoke.timer
"$RUNNER_PATH" status >/dev/null
printf 'timestamp=%s operation=bootstrap git_sha=%s result=PASS\n' \
  "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$initial_sha" >>"$LOG_ROOT/runner.log"

rm -f -- "$SOURCE_BUNDLE" "$SOURCE_SIGNATURE"
bootstrap_complete=true
printf 'BOOTSTRAP_PASS mission=%s git_sha=%s expires_epoch=%s\n' \
  "$MISSION_ID" "$initial_sha" "$expires_epoch"
printf 'MANUAL_REVOKE_COMMAND=sudo %s\n' "$REVOKE_PATH"
