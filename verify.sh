#!/usr/bin/env bash
set -uo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ ${1:-} == --repo ]]; then exec "$repo_dir/restore.sh" --dry-run; fi
result=0
check() { "$@" || result=1; }
check niri validate
check noctalia config validate
check fish -n "${XDG_CONFIG_HOME:-$HOME/.config}/fish/config.fish"
check systemctl is-active NetworkManager bluetooth power-profiles-daemon sddm
check systemctl --user is-active pipewire pipewire-pulse wireplumber
check wpctl status
check nmcli device status
check bluetoothctl show
check brightnessctl info
check xdg-settings get default-web-browser
check systemctl --failed --no-pager
check systemctl --user --failed --no-pager
exit "$result"
