#!/usr/bin/env python3
"""Float open Niri windows, then return the same windows to tiling."""

import fcntl
import json
import os
from pathlib import Path
import subprocess


def open_windows():
    result = subprocess.check_output(["niri", "msg", "--json", "windows"])
    return {window["id"]: window["is_floating"] for window in json.loads(result)}


def move_windows(window_ids, *, floating):
    action = "move-window-to-floating" if floating else "move-window-to-tiling"
    errors = []
    for window_id in window_ids:
        result = subprocess.run(
            ["niri", "msg", "action", action, "--id", str(window_id)],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            errors.append((window_id, result.stderr.strip()))

    # A window can close between listing it and sending the action.
    remaining = open_windows()
    failed = [
        window_id for window_id in window_ids
        if window_id in remaining and remaining[window_id] != floating
    ]
    if failed:
        details = [message for window_id, message in errors if window_id in failed and message]
        raise SystemExit("\n".join([f"Niri: {action} failed for windows {failed}", *details]))


def main():
    socket = Path(os.environ["NIRI_SOCKET"])
    session = f"{socket.name}.{socket.stat().st_ino}"
    state = Path(os.environ["XDG_RUNTIME_DIR"]) / f"{session}.floating-windows.json"

    with state.with_suffix(".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        windows = open_windows()
        if state.exists():
            previous = json.loads(state.read_text())
            move_windows([window_id for window_id in previous if windows.get(window_id)], floating=False)
            state.unlink()
        else:
            tiled = [window_id for window_id, floating in windows.items() if not floating]
            if tiled:
                pending = state.with_suffix(".tmp")
                pending.write_text(json.dumps(tiled))
                pending.replace(state)
                move_windows(tiled, floating=True)


if __name__ == "__main__":
    main()
