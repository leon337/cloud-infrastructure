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

for command in qemu-system-x86_64 qemu-img cloud-localds ssh scp ssh-keygen git curl sha256sum; do
  require_command "$command"
done

case "$(hostname --short)" in
  node-01 | vmi3506102) refuse real_dev_node ;;
esac

[[ -c /dev/kvm && -r /dev/kvm && -w /dev/kvm ]] || refuse kvm_access_unavailable
[[ $(git -C "$ROOT" rev-parse HEAD) == "$CANDIDATE_SHA" ]] || refuse candidate_not_head
[[ -z $(git -C "$ROOT" status --porcelain) ]] || refuse repository_not_clean

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

cleanup() {
  case $RUN_ROOT in
    "${TMPDIR:-/tmp}"/mcf-f1-2c-kvm.*) ;;
    *) printf '%s\n' 'KVM_LAB_CLEANUP_REFUSED invalid_run_root' >&2; return 1 ;;
  esac
  rm -f -- "$RUN_ROOT"/candidate.bundle "$RUN_ROOT"/seed.img "$RUN_ROOT"/overlay.qcow2 \
    "$RUN_ROOT"/id_ed25519 "$RUN_ROOT"/id_ed25519.pub "$RUN_ROOT"/qemu.pid
  rmdir -- "$RUN_ROOT" 2>/dev/null || true
}
trap cleanup EXIT INT TERM HUP

printf 'KVM_LAB_PREFLIGHT=PASS candidate=%s\n' "$CANDIDATE_SHA"
