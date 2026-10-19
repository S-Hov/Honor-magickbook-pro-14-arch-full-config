#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
(( EUID != 0 )) || { echo 'Запускайте без sudo.' >&2; exit 1; }
if [[ ${1:-} == --dry-run && $# -eq 1 ]]; then
    "$repo_dir/restore.sh" --dry-run
    "$repo_dir/install-system.sh" --dry-run
    exit 0
fi
if (( $# )); then echo 'Для ACPI используйте отдельно: sudo ./install-system.sh --acpi' >&2; exit 1; fi
"$repo_dir/install-packages.sh"
"$repo_dir/restore.sh"
sudo "$repo_dir/install-system.sh"
systemctl --user daemon-reload
systemctl --user enable --now pipewire.socket pipewire-pulse.socket wireplumber.service
"$repo_dir/verify.sh"
echo 'Готово. Темы GRUB и SDDM применятся после перезагрузки.'
