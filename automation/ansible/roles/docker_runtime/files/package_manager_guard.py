#!/usr/bin/env python3
"""Report real APT/dpkg activity without flagging the idle shutdown watcher."""

from __future__ import annotations

import json
import os
from pathlib import Path


PACKAGE_COMMANDS = {
    "apt",
    "apt-get",
    "apt.systemd.daily",
    "dpkg",
    "unattended-upgrade",
}
PACKAGE_COMMS = {
    "apt",
    "apt-get",
    "apt.systemd.dai",
    "dpkg",
    "unattended-upgr",
    "unattended-upgrade",
}


def classify_process(comm: str, argv: list[str]) -> str | None:
    """Return a safe activity label, or None for unrelated/idle processes."""
    basenames = {os.path.basename(argument) for argument in argv}
    if (
        "unattended-upgrade-shutdown" in basenames
        and "--wait-for-signal" in argv
    ):
        return None
    commands = basenames & PACKAGE_COMMANDS
    if comm not in PACKAGE_COMMS and not commands:
        return None
    return sorted(commands)[0] if commands else comm


def inspect_processes(proc_root: Path = Path("/proc")) -> dict[str, object]:
    active: list[dict[str, object]] = []
    ignored_watchers = 0
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            comm = (entry / "comm").read_text(encoding="utf-8").strip()
            argv = [
                value.decode("utf-8", errors="replace")
                for value in (entry / "cmdline").read_bytes().split(b"\0")
                if value
            ]
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        basenames = {os.path.basename(argument) for argument in argv}
        if (
            "unattended-upgrade-shutdown" in basenames
            and "--wait-for-signal" in argv
        ):
            ignored_watchers += 1
            continue
        label = classify_process(comm, argv)
        if label is not None:
            active.append({"command": label, "pid": int(entry.name)})
    return {
        "active": sorted(active, key=lambda item: int(item["pid"])),
        "ignored_idle_shutdown_watchers": ignored_watchers,
    }


if __name__ == "__main__":
    print(json.dumps(inspect_processes(), sort_keys=True, separators=(",", ":")))
