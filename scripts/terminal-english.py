#!/usr/bin/env python3
"""Select English when a Kitty window gains focus in Niri."""
import json
import subprocess


def main():
    windows = {}
    focused = None

    def focus(window_id):
        nonlocal focused
        changed = window_id != focused
        focused = window_id
        if changed and windows.get(window_id, {}).get("app_id") == "kitty":
            # Recheck live focus: queued events must not affect another app.
            current = json.loads(subprocess.check_output(
                ["niri", "msg", "-j", "focused-window"], text=True, timeout=3
            ))
            if current and current["id"] == window_id:
                subprocess.run(
                    ["niri", "msg", "action", "switch-layout", "0"],
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
