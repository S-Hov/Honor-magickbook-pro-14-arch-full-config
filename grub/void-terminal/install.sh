#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then
    exec sudo bash "$0" "$@"
fi
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
backup_dir="/var/backups/grub-void-terminal-$(date +%Y%m%d-%H%M%S)"
target_dir=/boot/grub/themes/void-terminal
for command_name in grub-mkconfig grub-script-check python3; do
    command -v "$command_name" >/dev/null
done
[[ -f /etc/default/grub && -f /boot/grub/grub.cfg ]]
mkdir -p "$backup_dir" "$target_dir"
cp -a /etc/default/grub "$backup_dir/default-grub"
cp -a /boot/grub/grub.cfg "$backup_dir/grub.cfg"
if [[ -e "$target_dir/theme.txt" ]]; then
    cp -a "$target_dir" "$backup_dir/previous-theme"
fi
rollback() {
    cp -a "$backup_dir/default-grub" /etc/default/grub
    cp -a "$backup_dir/grub.cfg" /boot/grub/grub.cfg
    rm -f /boot/grub/grub.cfg.void-terminal-new
    printf 'Configuration restored from %s\n' "$backup_dir" >&2
}
trap rollback ERR
install -m644 "$source_dir/theme.txt" "$source_dir/background.png" "$source_dir"/*.pf2 "$source_dir"/select_*.png "$source_dir/FONT-LICENSE.txt" "$target_dir/"
install -d "$target_dir/icons"
install -m644 "$source_dir"/icons/*.png "$target_dir/icons/"
python3 - <<'PY'
from pathlib import Path
import re
p=Path('/etc/default/grub')
lines=[line for line in p.read_text().splitlines() if not re.match(r'^\s*GRUB_(THEME|GFXMODE)=',line)]
lines += ['', 'GRUB_THEME="/boot/grub/themes/void-terminal/theme.txt"', 'GRUB_GFXMODE="1920x1080,auto"']
p.write_text('\n'.join(lines)+'\n')
PY
grub-mkconfig -o /boot/grub/grub.cfg.void-terminal-new
# The stock UEFI generator emits no class. Add a presentation-only class.
python3 - <<'PYICON'
from pathlib import Path
p=Path('/boot/grub/grub.cfg.void-terminal-new')
lines=p.read_text().splitlines(keepends=True)
for i,line in enumerate(lines):
    if line.lstrip().startswith('menuentry ') and "'uefi-firmware'" in line and '--class' not in line:
        lines[i]=line.replace('menuentry ', 'menuentry --class firmware ', 1)
p.write_text(''.join(lines))
PYICON
grub-script-check /boot/grub/grub.cfg.void-terminal-new
mv /boot/grub/grub.cfg.void-terminal-new /boot/grub/grub.cfg
trap - ERR
printf 'Void Terminal installed. Backup: %s\n' "$backup_dir"
