#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON=${PYTHON:-python3}
REQUIRE_ANSIBLE=${REQUIRE_ANSIBLE:-0}
REQUIRE_SHELLCHECK=${REQUIRE_SHELLCHECK:-0}

cd "$REPOSITORY_ROOT"

"$PYTHON" scripts/check_repository_secrets.py
"$PYTHON" scripts/check_markdown_links.py
"$PYTHON" scripts/validate_yaml.py
"$PYTHON" scripts/validate_manifests.py
"$PYTHON" scripts/validate_state.py
"$PYTHON" - <<'PY'
import sys
import unittest

suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():
    raise SystemExit(1)
print(f"UNIT_TESTS_PASS count={result.testsRun}")
PY
"$PYTHON" -m compileall -q scripts tests

shell_scripts=()
shell_script_count=0
while IFS= read -r -d '' path; do
  if [[ ! -f "$path" ]] || ! head -c 2 -- "$path" | cmp -s - <(printf '#!'); then
    continue
  fi
  IFS= read -r first_line < "$path" || true
  case "$first_line" in
    '#!'*bash*)
      bash -n "$path"
      shell_scripts+=("$path")
      shell_script_count=$((shell_script_count + 1))
      ;;
    '#!'*/sh | '#!'*' sh')
      sh -n "$path"
      shell_scripts+=("$path")
      shell_script_count=$((shell_script_count + 1))
      ;;
  esac
done < <(git ls-files --cached --others --exclude-standard -z)
printf 'SHELL_SYNTAX_PASS count=%s\n' "$shell_script_count"

if command -v ansible-playbook >/dev/null 2>&1; then
  (
    cd automation/ansible
    shopt -s nullglob
    playbooks=(playbooks/*.yml playbooks/*.yaml)
    if ((${#playbooks[@]} == 0)); then
      printf '%s\n' 'TEST_FAIL no Ansible playbooks found' >&2
      exit 1
    fi
    for playbook in "${playbooks[@]}"; do
      ansible-playbook "$playbook" --syntax-check
    done
    printf 'ANSIBLE_SYNTAX_PASS count=%s\n' "${#playbooks[@]}"
  )
else
  if [[ "$REQUIRE_ANSIBLE" == 1 ]]; then
    printf '%s\n' 'TEST_FAIL ansible-playbook is required but not installed' >&2
    exit 1
  fi
  printf '%s\n' 'TEST_SKIP ansible-playbook is not installed (optional on this controller)'
fi

if command -v shellcheck >/dev/null 2>&1; then
  shellcheck "${shell_scripts[@]}"
  printf 'SHELLCHECK_PASS count=%s\n' "$shell_script_count"
else
  if [[ "$REQUIRE_SHELLCHECK" == 1 ]]; then
    printf '%s\n' 'TEST_FAIL shellcheck is required but not installed' >&2
    exit 1
  fi
  printf '%s\n' 'TEST_SKIP shellcheck is not installed (optional on this controller)'
fi

printf '%s\n' 'FOUNDATION_STATIC_TESTS_PASS'
