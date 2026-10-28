#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
(( EUID != 0 )) || { echo 'Запускайте без sudo.' >&2; exit 1; }
install -Dm644 "$repo_dir/scripts/terminal-english.py" "$HOME/.local/lib/terminal-english.py"
install -Dm644 "$repo_dir/systemd/user/terminal-english.service" "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/terminal-english.service"
systemctl --user daemon-reload
systemctl --user enable --now terminal-english.service
echo 'Готово. При открытии Kitty и возвращении в его окно включается английская раскладка.'
