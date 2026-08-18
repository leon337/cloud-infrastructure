#!/usr/bin/env python3
"""Render lightweight project status from canonical repository state."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from yaml_strict import load_strict  # noqa: E402


README = ROOT / "README.md"
CURRENT = ROOT / "state/current.yaml"
COMPONENTS = ROOT / "state/components.yaml"
ROADMAP = ROOT / "docs/45-revised-implementation-roadmap.md"
START = "<!-- PROJECT_STATUS:START -->"
END = "<!-- PROJECT_STATUS:END -->"
ALLOWED_STATES = {
    "PLANNED",
    "IMPLEMENTING",
    "WAITING_HUMAN_GATE",
    "CONDITIONAL",
    "PARTIAL",
    "DONE",
}
PROJECT_COLUMNS = {
    "PLANNED": "TODO",
    "IMPLEMENTING": "IN PROGRESS",
    "WAITING_HUMAN_GATE": "HUMAN GATE",
    "CONDITIONAL": "TODO",
    "PARTIAL": "VALIDATING",
    "DONE": "DONE",
}


def mapping(path: pathlib.Path) -> dict[str, Any]:
    value = load_strict(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a mapping")
    return value


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid canonical field: {field}")
    return value.strip()


def roadmap_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4 or cells[0] in {"Slice", ""}:
            continue
        status = cells[2].strip("`")
        if status not in ALLOWED_STATES:
            raise ValueError(f"unsupported roadmap state {status!r} for {cells[0]}")
        rows.append(
            {
                "slice": cells[0],
                "result": cells[1],
                "status": status,
                "gate": cells[3],
                "project_column": PROJECT_COLUMNS[status],
            }
        )
    if not rows:
        raise ValueError("canonical roadmap has no slice rows")
    return rows


def normalized_status() -> dict[str, Any]:
    current = mapping(CURRENT)
    components = mapping(COMPONENTS)
    rows = roadmap_rows(ROADMAP.read_text(encoding="utf-8"))
    project = current.get("project", {})
    authorization = current.get("authorization", {})
    layer = current.get("status_layer", {})
    execution = current.get("codex_execution", {})

    if project.get("credential_rotation") != "DEFERRED_BY_HUMAN_DECISION":
        raise ValueError("credential rotation guard drifted")
    if authorization.get("production_promotion") != "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED":
        raise ValueError("production authorization guard drifted")
    if components.get("environment") != "DEV_LAB":
        raise ValueError("component inventory is not DEV_LAB")

    current_id = require_text(layer.get("current_slice_id"), "status_layer.current_slice_id")
    current_name = require_text(layer.get("current_slice_name"), "status_layer.current_slice_name")
    matches = [row for row in rows if row["slice"].startswith(current_id + " ")]
    if len(matches) != 1:
        raise ValueError(f"current slice {current_id!r} is not unique in roadmap")
    current_row = matches[0]
    done = [row for row in rows if row["status"] == "DONE"]
    gates = [row for row in rows if row["status"] == "WAITING_HUMAN_GATE"]
    current_index = rows.index(current_row)
    upcoming = rows[current_index + 1 : current_index + 4]

    return {
        "project_status": require_text(layer.get("project_status"), "status_layer.project_status"),
        "current_slice": current_id,
        "current_slice_name": current_name,
        "current_slice_status": current_row["status"],
        "done": done,
        "upcoming": upcoming,
        "human_gates": gates,
        "next_exact_step": require_text(project.get("next_exact_step"), "project.next_exact_step"),
        "production": authorization["production_promotion"],
        "credential_rotation": project["credential_rotation"],
        "updated_at": str(current.get("updated_at")),
        "last_checkpoint": require_text(layer.get("last_material_checkpoint"), "status_layer.last_material_checkpoint"),
        "last_commit": require_text(layer.get("last_relevant_commit"), "status_layer.last_relevant_commit"),
        "last_ci_run_id": layer.get("last_ci_run_id"),
        "last_ci_conclusion": require_text(layer.get("last_ci_conclusion"), "status_layer.last_ci_conclusion"),
        "github_project": require_text(layer.get("github_project"), "status_layer.github_project"),
        "slices": rows,
    }


def readme_block(status: dict[str, Any]) -> str:
    completed = ", ".join(row["slice"].split(" ", 1)[0] for row in status["done"])
    gates = ", ".join(row["slice"].split(" ", 1)[0] for row in status["human_gates"])
    upcoming = ", ".join(row["slice"].split(" ", 1)[0] for row in status["upcoming"])
    run = status["last_ci_run_id"]
    return "\n".join(
        (
            START,
            "## STATUS ATUAL",
            "",
            f"- **Status geral:** `{status['project_status']}`",
            f"- **Progresso:** {len(status['done'])}/{len(status['slices'])} slices `DONE`; slice atual `PARTIAL`",
            f"- **Slice atual:** `{status['current_slice']}` — {status['current_slice_name']}",
            f"- **Concluídos:** {completed}",
            f"- **Próximos:** {upcoming}",
            f"- **HUMAN_GATEs no roadmap:** {len(status['human_gates'])} ({gates})",
            f"- **Próximo passo exato:** `{status['next_exact_step']}`",
            f"- **Último checkpoint:** `{status['last_checkpoint']}`",
            f"- **Último commit relevante:** [`{status['last_commit'][:7]}`](https://github.com/leon337/cloud-infrastructure/commit/{status['last_commit']})",
            f"- **Última CI material:** [run `{run}`](https://github.com/leon337/cloud-infrastructure/actions/runs/{run}) — `{status['last_ci_conclusion']}`",
            f"- **GitHub Project:** `{status['github_project']}`",
            f"- **Produção:** `{status['production']}`",
            f"- **Rotação de credenciais:** `{status['credential_rotation']}`",
            f"- **Atualizado em:** `{status['updated_at']}`",
            "",
            "> Esta seção é gerada das fontes canônicas; não edite manualmente.",
            END,
        )
    )


def update_readme(block: str, check: bool) -> None:
    original = README.read_text(encoding="utf-8")
    if START in original or END in original:
        if original.count(START) != 1 or original.count(END) != 1:
            raise ValueError("README status markers are incomplete or duplicated")
        pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
        rendered = pattern.sub(block, original)
    else:
        heading_end = original.find("\n", original.find("# "))
        rendered = original[: heading_end + 1] + "\n" + block + "\n" + original[heading_end + 1 :]
    if check:
        if rendered != original:
            raise ValueError("README generated status is stale; run --write-readme")
    elif rendered != original:
        README.write_text(rendered, encoding="utf-8")


def write_summary(path: pathlib.Path, status: dict[str, Any], tests: str, commit: str, timestamp: str) -> None:
    text = "\n".join(
        (
            "## Cloud Infrastructure — Mission Status",
            "",
            f"| Field | Value |",
            "|---|---|",
            f"| Current Slice | `{status['current_slice']}` — {status['current_slice_name']} |",
            f"| Project Status | `{status['project_status']}` |",
            f"| Tests | `{tests}` |",
            f"| HUMAN_GATEs | `{len(status['human_gates'])}` |",
            f"| Next Exact Step | `{status['next_exact_step']}` |",
            f"| Commit SHA | `{commit}` |",
            f"| Updated | `{timestamp}` |",
            "",
        )
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-readme", action="store_true")
    parser.add_argument("--check-readme", action="store_true")
    parser.add_argument("--summary", type=pathlib.Path)
    parser.add_argument("--tests-result", choices=("PASS", "FAIL"), default="PASS")
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "LOCAL"))
    parser.add_argument("--timestamp", default="CANONICAL_STATE_DATE")
    parser.add_argument("--project-json", type=pathlib.Path)
    args = parser.parse_args()
    if args.write_readme and args.check_readme:
        parser.error("choose only one README mode")

    status = normalized_status()
    block = readme_block(status)
    if args.write_readme or args.check_readme:
        update_readme(block, args.check_readme)
    if args.summary:
        write_summary(args.summary, status, args.tests_result, args.commit, args.timestamp)
    if args.project_json:
        args.project_json.write_text(
            json.dumps({"title": "IMPLEMENTAÇÃO DA VPS", "private": True, "items": status["slices"]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        f"PROJECT_STATUS_PASS current={status['current_slice']} "
        f"done={len(status['done'])}/{len(status['slices'])} gates={len(status['human_gates'])}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, TypeError, ValueError) as exc:
        print(f"PROJECT_STATUS_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
