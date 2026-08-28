#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON=${PYTHON:-python3}
REQUIRE_SHELLCHECK=${REQUIRE_SHELLCHECK:-0}
VALIDATION_BASE_REF=${VALIDATION_BASE_REF:-}
export PYTHONDONTWRITEBYTECODE=1

cd "$REPOSITORY_ROOT"

if [[ -n "$VALIDATION_BASE_REF" ]]; then
  git diff --check "$VALIDATION_BASE_REF"...HEAD
  printf 'GIT_DIFF_CHECK_PASS base=%s\n' "$VALIDATION_BASE_REF"
else
  git diff --check
  printf '%s\n' 'GIT_DIFF_CHECK_PASS base=working-tree'
fi

"$PYTHON" scripts/check_repository_secrets.py
"$PYTHON" scripts/check_runner_isolation.py
"$PYTHON" scripts/check_markdown_links.py
"$PYTHON" scripts/validate_yaml.py
"$PYTHON" scripts/validate_state.py
"$PYTHON" scripts/check_canonical_consistency.py

"$PYTHON" -m unittest discover -s tests -p 'test_*.py' -v

"$PYTHON" - <<'PY'
from pathlib import Path
import subprocess

paths = subprocess.check_output(["git", "ls-files", "*.py"], text=True).splitlines()
for path_text in paths:
    path = Path(path_text)
    compile(path.read_text(encoding="utf-8"), path_text, "exec")
print(f"PYTHON_SYNTAX_PASS count={len(paths)}")
PY

shell_scripts=()
shell_script_count=0
while IFS= read -r -d '' path; do
  [[ -f "$path" ]] || continue
  IFS= read -r first_line < "$path" || true
  case "$first_line" in
    '#!'*bash*) bash -n "$path" ;;
    '#!'*/sh | '#!'*' sh') sh -n "$path" ;;
    *) continue ;;
  esac
  shell_scripts+=("$path")
  shell_script_count=$((shell_script_count + 1))
done < <(git ls-files -z)
printf 'SHELL_SYNTAX_PASS count=%s\n' "$shell_script_count"

if command -v shellcheck >/dev/null 2>&1; then
  if ((${#shell_scripts[@]} > 0)); then
    shellcheck "${shell_scripts[@]}"
  fi
  printf 'SHELLCHECK_PASS count=%s\n' "$shell_script_count"
elif [[ "$REQUIRE_SHELLCHECK" == 1 ]]; then
  printf '%s\n' 'TEST_FAIL shellcheck is required but not installed' >&2
  exit 1
else
  printf '%s\n' 'TEST_SKIP shellcheck is not installed (optional outside CI)'
fi

printf '%s\n' 'CANONICAL_VALIDATION_PASS'
