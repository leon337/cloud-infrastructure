#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly IMAGE_ENV="$ROOT/platform/kvm/f1-2c-ubuntu-24.04-amd64.env"

refuse() { printf 'KVM_LAB_REFUSED reason=%s\n' "$1" >&2; exit 2; }

[[ $# -eq 1 ]] || refuse exactly_one_candidate_sha_required
[[ $1 =~ ^[0-9a-f]{40}$ ]] || refuse invalid_candidate_sha
readonly CANDIDATE_SHA=$1

# shellcheck disable=SC1090
source "$IMAGE_ENV"

require_command() {
  command -v "$1" >/dev/null 2>&1 || refuse "missing_command_$1"
}

for command in \
  qemu-system-x86_64 qemu-img cloud-localds ssh scp ssh-keygen git curl sha256sum \
  od tr sed python3 awk df seq sleep stat kill; do
  require_command "$command"
done

case "$(hostname --short)" in
  node-01 | vmi3506102) refuse real_dev_node ;;
esac

[[ -c /dev/kvm && -r /dev/kvm && -w /dev/kvm ]] || refuse kvm_access_unavailable
[[ $(git -C "$ROOT" rev-parse HEAD) == "$CANDIDATE_SHA" ]] || refuse candidate_not_head
[[ -z $(git -C "$ROOT" status --porcelain) ]] || refuse repository_not_clean

mem_kib=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
[[ $mem_kib =~ ^[0-9]+$ ]] || refuse host_memory_probe_failed
(( mem_kib >= 5 * 1024 * 1024 )) || refuse insufficient_host_memory
free_kib=$(df -Pk "${TMPDIR:-/tmp}" | awk 'NR==2 {print $4}')
[[ $free_kib =~ ^[0-9]+$ ]] || refuse host_disk_probe_failed
(( free_kib >= 30 * 1024 * 1024 )) || refuse insufficient_host_disk

readonly CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/mcf-kvm-lab"
readonly BASE_IMAGE="$CACHE_DIR/$MCF_KVM_IMAGE_NAME"
mkdir -p -m 0700 "$CACHE_DIR"

verify_image() {
  printf '%s  %s\n' "$MCF_KVM_IMAGE_SHA256" "$1" | sha256sum --check --status
}

if [[ -e $BASE_IMAGE ]]; then
  [[ -f $BASE_IMAGE && ! -L $BASE_IMAGE ]] || refuse invalid_cached_image_type
  verify_image "$BASE_IMAGE" || refuse cached_image_digest_mismatch
else
  download="$CACHE_DIR/.${MCF_KVM_IMAGE_NAME}.$$"
  trap 'rm -f -- "$download"' RETURN
  curl --fail --location --proto '=https' --tlsv1.2 --output "$download" "$MCF_KVM_IMAGE_URL"
  verify_image "$download" || refuse downloaded_image_digest_mismatch
  chmod 0600 "$download"
  mv -- "$download" "$BASE_IMAGE"
  trap - RETURN
fi

readonly RUN_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/mcf-f1-2c-kvm.XXXXXXXX")
readonly EVIDENCE_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/mcf-kvm-lab/evidence"
readonly EVIDENCE_DIR="$EVIDENCE_ROOT/$(date -u +%Y%m%dT%H%M%SZ)-${CANDIDATE_SHA:0:12}"
mkdir -p -m 0700 "$EVIDENCE_DIR"

qemu_pid_is_ours() {
  local pid cmdline owner_uid
  [[ -f $RUN_ROOT/qemu.pid && ! -L $RUN_ROOT/qemu.pid ]] || return 1
  IFS= read -r pid <"$RUN_ROOT/qemu.pid" || return 1
  [[ $pid =~ ^[0-9]+$ ]] || return 1
  [[ -d /proc/$pid && -r /proc/$pid/cmdline ]] || return 1
  owner_uid=$(stat -c '%u' "/proc/$pid") || return 1
  [[ $owner_uid == "$EUID" ]] || return 1
  cmdline=$(tr '\0' ' ' <"/proc/$pid/cmdline") || return 1
  [[ $cmdline == *"$RUN_ROOT/overlay.qcow2"* ]]
}

stop_qemu() {
  local pid
  [[ -e $RUN_ROOT/qemu.pid ]] || return 0
  IFS= read -r pid <"$RUN_ROOT/qemu.pid" || {
    printf '%s\n' 'KVM_LAB_CLEANUP_REFUSED invalid_qemu_pid_file' >&2
    return 1
  }
  [[ $pid =~ ^[0-9]+$ ]] || {
    printf '%s\n' 'KVM_LAB_CLEANUP_REFUSED invalid_qemu_pid' >&2
    return 1
  }
  [[ -d /proc/$pid ]] || return 0
  qemu_pid_is_ours || {
    printf '%s\n' 'KVM_LAB_CLEANUP_REFUSED qemu_pid_not_owned_by_run' >&2
    return 1
  }
  kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 1 20); do
    [[ -d /proc/$pid ]] || return 0
    sleep 0.25
  done
  if [[ -d /proc/$pid ]]; then
    qemu_pid_is_ours || {
      printf '%s\n' 'KVM_LAB_CLEANUP_REFUSED qemu_pid_changed_before_kill' >&2
      return 1
    }
    kill -KILL "$pid" 2>/dev/null || true
  fi
}

cleanup() {
  case $RUN_ROOT in
    "${TMPDIR:-/tmp}"/mcf-f1-2c-kvm.*) ;;
    *) printf '%s\n' 'KVM_LAB_CLEANUP_REFUSED invalid_run_root' >&2; return 1 ;;
  esac
  stop_qemu || return 1
  rm -f -- "$RUN_ROOT"/candidate.bundle "$RUN_ROOT"/seed.img "$RUN_ROOT"/overlay.qcow2 \
    "$RUN_ROOT"/id_ed25519 "$RUN_ROOT"/id_ed25519.pub "$RUN_ROOT"/qemu.pid \
    "$RUN_ROOT"/user-data "$RUN_ROOT"/meta-data "$RUN_ROOT"/serial.log
  rmdir -- "$RUN_ROOT" 2>/dev/null || true
}
trap cleanup EXIT INT TERM HUP

readonly RUN_ID=$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')
readonly GUEST_HOSTNAME="mcf-f1-2c-kvm-$RUN_ID"
readonly SSH_KEY="$RUN_ROOT/id_ed25519"
ssh-keygen -q -t ed25519 -N '' -f "$SSH_KEY"
chmod 0600 "$SSH_KEY"

ssh_pub=$(<"$SSH_KEY.pub")
sed \
  -e "s|__MCF_KVM_RUN_ID__|$RUN_ID|g" \
  -e "s|__MCF_KVM_SSH_PUBLIC_KEY__|$ssh_pub|g" \
  "$ROOT/platform/kvm/f1-2c-cloud-init-user-data.yaml.in" >"$RUN_ROOT/user-data"
sed "s|__MCF_KVM_RUN_ID__|$RUN_ID|g" \
  "$ROOT/platform/kvm/f1-2c-cloud-init-meta-data.yaml.in" >"$RUN_ROOT/meta-data"
cloud-localds "$RUN_ROOT/seed.img" "$RUN_ROOT/user-data" "$RUN_ROOT/meta-data"

qemu-img create -q -f qcow2 -F qcow2 -b "$BASE_IMAGE" "$RUN_ROOT/overlay.qcow2" 24G

SSH_PORT=$(python3 - <<'PY'
import socket

sock = socket.socket()
sock.bind(("127.0.0.1", 0))
print(sock.getsockname()[1])
sock.close()
PY
)
readonly SSH_PORT

qemu-system-x86_64 \
  -enable-kvm -cpu host -smp 2 -m 4096 \
  -drive "file=$RUN_ROOT/overlay.qcow2,if=virtio,format=qcow2" \
  -drive "file=$RUN_ROOT/seed.img,if=virtio,format=raw,readonly=on" \
  -nic "user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:${SSH_PORT}-:22" \
  -display none -serial "file:$RUN_ROOT/serial.log" \
  -daemonize -pidfile "$RUN_ROOT/qemu.pid"

[[ -s $RUN_ROOT/qemu.pid ]] || refuse qemu_pid_missing
qemu_pid_is_ours || refuse qemu_identity_verification_failed

SSH=(
  ssh -i "$SSH_KEY" -p "$SSH_PORT" -o BatchMode=yes
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
  -o ConnectTimeout=3 mcf-lab@127.0.0.1
)

guest_ready=0
for _ in $(seq 1 120); do
  if "${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1 && systemctl is-active --quiet docker.service'; then
    guest_ready=1
    break
  fi
  sleep 2
done
[[ $guest_ready == 1 ]] || refuse guest_readiness_timeout

printf 'KVM_LAB_GUEST_READY candidate=%s run_id=%s guest=%s ssh_port=%s\n' \
  "$CANDIDATE_SHA" "$RUN_ID" "$GUEST_HOSTNAME" "$SSH_PORT"
