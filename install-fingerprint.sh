#!/usr/bin/env bash
# Optional driver for the EgisTec 1c7a:05aa reader. Run as the target user.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
(( EUID != 0 )) || { echo 'Запустите без sudo: сборка выполняется обычным пользователем.' >&2; exit 1; }
lsusb -d 1c7a:05aa | grep -q . || { echo 'Сканер 1c7a:05aa не найден; установка отменена.' >&2; exit 1; }
sudo pacman -S --needed fprintd libfprint meson ninja glib2-devel libgusb pkgconf git base-devel
mkdir -p "${XDG_CACHE_HOME:-$HOME/.cache}"
build_dir=$(mktemp -d "${XDG_CACHE_HOME:-$HOME/.cache}/honor-fingerprint.XXXXXX")
cp -a "$repo_dir/hardware/fingerprint/." "$build_dir/"
cd "$build_dir"
makepkg --cleanbuild
package=$(makepkg --packagelist | awk '!/-debug-/ {print; exit}')
[[ -f "$package" ]] || { echo 'Пакет драйвера не найден.' >&2; exit 1; }
sudo pacman -U "$package"
sudo systemctl restart fprintd
fprintd-list "$USER"
printf '\nДрайвер установлен. Запишите и проверьте отпечаток:\n  fprintd-enroll -f right-index-finger\n  fprintd-verify\n\nNoctalia поддерживает fprintd напрямую. PAM автоматически не меняется.\nИнструкция: %s/docs/FINGERPRINT.md\nСборка сохранена: %s\n' "$repo_dir" "$build_dir"
