#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
(( EUID != 0 )) || { echo 'Запускайте без sudo, от обычного пользователя.' >&2; exit 1; }
mapfile -t official < <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' "$repo_dir/packages/official.txt")
sudo pacman -Syu --needed "${official[@]}"
if command -v paru >/dev/null; then helper=paru
elif command -v yay >/dev/null; then helper=yay
else
    build_dir=$(mktemp -d -t honor-yay-XXXXXXXX)
    echo "Для AUR нужен helper. Сборка yay: $build_dir (PKGBUILD можно проверить перед makepkg)."
    git clone https://aur.archlinux.org/yay.git "$build_dir/yay"
    less "$build_dir/yay/PKGBUILD"
    (cd "$build_dir/yay" && makepkg -si)
    helper=yay
fi
mapfile -t aur < <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' "$repo_dir/packages/aur.txt")
"$helper" -S --needed "${aur[@]}"
