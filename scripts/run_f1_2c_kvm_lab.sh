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

printf 'KVM_LAB_PREFLIGHT=PASS candidate=%s\n' "$CANDIDATE_SHA"
