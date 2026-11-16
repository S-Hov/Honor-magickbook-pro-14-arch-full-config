#!/usr/bin/env python3
"""Use English in Kitty and restore the previous layout when leaving it."""
import json
import subprocess


def main():
    windows = {}
    focused = None
    previous_layout = None

    def focus(window_id):
        nonlocal focused, previous_layout
        if window_id == focused:
            return
        # Keep the saved layout through temporary lack of window focus (menus,
        # launchers, closing a window) until another application gets focus.
        if window_id is None:
            focused = None
            return
        if window_id not in windows:
            return
        # Recheck live focus: queued events must not affect another app.
        current = json.loads(subprocess.check_output(
            ["niri", "msg", "-j", "focused-window"], text=True, timeout=3
        ))
        if not current or current["id"] != window_id:
            return
        focused = window_id
        if windows[window_id].get("app_id") == "kitty":
            # Moving between terminal windows must not overwrite the layout
            # saved before entering the first terminal.
            if previous_layout is None:
                previous_layout = json.loads(subprocess.check_output(
                    ["niri", "msg", "-j", "keyboard-layouts"], text=True, timeout=3
                ))["current_idx"]
            target_layout = 0
        elif previous_layout is not None:
            target_layout = previous_layout
            previous_layout = None
        else:
            return
        subprocess.run(
            ["niri", "msg", "action", "switch-layout", str(target_layout)],
            check=True, timeout=3,
        )

    with subprocess.Popen(
        ["niri", "msg", "-j", "event-stream"], stdout=subprocess.PIPE, text=True
    ) as stream:
        try:
            for line in stream.stdout:
                event = json.loads(line)
                if "WindowsChanged" in event:
                    windows = {w["id"]: w for w in event["WindowsChanged"]["windows"]}
                    focus(next((w["id"] for w in windows.values() if w["is_focused"]), None))
                elif "WindowOpenedOrChanged" in event:
                    window = event["WindowOpenedOrChanged"]["window"]
                    windows[window["id"]] = window
                    if window["is_focused"]:
                        focus(window["id"])
                elif "WindowFocusChanged" in event:
                    focus(event["WindowFocusChanged"]["id"])
                elif "WindowClosed" in event:
                    windows.pop(event["WindowClosed"]["id"], None)
        finally:
            if stream.poll() is None:
                stream.terminate()
        stream.wait()
        raise SystemExit(stream.returncode or 1)


if __name__ == "__main__":
    main()
