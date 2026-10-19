#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
with_acpi=0
case "${1:-}" in
    '') ;;
    --acpi) with_acpi=1 ;;
    --dry-run) echo 'Установка: GRUB CyberEXS, SDDM Sumi Red, NetworkManager, Bluetooth, PPD, ALSA. ACPI только с --acpi.'; exit 0 ;;
    *) echo 'Использование: sudo ./install-system.sh [--acpi]' >&2; exit 1 ;;
esac
(( EUID == 0 )) || { echo 'Нужен sudo.' >&2; exit 1; }
# Do not replace another display manager or terminate its session.
if [[ -L /etc/systemd/system/display-manager.service ]] && [[ $(readlink -f /etc/systemd/system/display-manager.service) != /usr/lib/systemd/system/sddm.service ]]; then
    echo 'Обнаружен другой display manager. Сначала отключите его вручную.' >&2; exit 1
fi
if (( with_acpi )); then
    python3 - "$repo_dir" <<'PY'
import pathlib,json,hashlib,sys
r=pathlib.Path(sys.argv[1]);m=json.loads((r/'hardware/machine.json').read_text())
for file,key in [('sys_vendor','vendor'),('product_name','product'),('product_version','version'),('bios_version','bios')]:
    actual=(pathlib.Path('/sys/class/dmi/id')/file).read_text().strip()
    if actual!=m[key]:raise SystemExit(f'ACPI: {file}={actual!r}, требуется {m[key]!r}. Установка отменена.')
b=(r/'hardware/acpi/SSDT27_TPD0.aml').read_bytes()
if hashlib.sha256(b).hexdigest()!=m['acpi_sha256'] or sum(b)%256 or b[:4]!=b'SSDT':
    raise SystemExit('ACPI: контрольная сумма таблицы неверна.')
PY
fi
backup="/var/backups/arch-honor-config-$(date +%Y%m%d-%H%M%S)"
install -d -m755 "$backup/files"
paths=(/etc/udev/rules.d/99-honor-focaltech-phantom-mic.rules /etc/grub.d/29_honor_windows /etc/default/grub /boot/grub/grub.cfg /etc/sddm.conf.d/90-sumi-red.conf /etc/mkinitcpio.conf /etc/initcpio/install/acpi_override /usr/lib/firmware/acpi/SSDT27_TPD0.aml)
for file in "${paths[@]}"; do
    if [[ -e "$file" ]]; then
        install -d "$backup/files$(dirname "$file")"
        cp -a "$file" "$backup/files$file"
    fi
done
printf '%s\n' "$backup" > /var/backups/arch-honor-config-last
install -d -m755 /boot/grub/themes /usr/share/sddm/themes /etc/sddm.conf.d
[[ ! -d /boot/grub/themes/CyberEXS ]] || cp -a /boot/grub/themes/CyberEXS "$backup/previous-CyberEXS"
[[ ! -d /usr/share/sddm/themes/sumi-red ]] || cp -a /usr/share/sddm/themes/sumi-red "$backup/previous-sumi-red"
cp -a "$repo_dir/grub/CyberEXS" /boot/grub/themes/
cp -a "$repo_dir/sddm/sumi-red" /usr/share/sddm/themes/
chown -R root:root /boot/grub/themes/CyberEXS /usr/share/sddm/themes/sumi-red
chmod -R a+rX /boot/grub/themes/CyberEXS /usr/share/sddm/themes/sumi-red
install -m644 "$repo_dir/sddm/90-sumi-red.conf" /etc/sddm.conf.d/90-sumi-red.conf
if [[ -f /etc/default/grub && -f /boot/grub/grub.cfg ]]; then
    install -o root -g root -m755 "$repo_dir/grub/29_honor_windows" /etc/grub.d/29_honor_windows
    python3 - <<'PY'
from pathlib import Path
import re
p=Path('/etc/default/grub');s=p.read_text()
for key,val in {'GRUB_THEME':'"/boot/grub/themes/CyberEXS/theme.txt"','GRUB_GFXMODE':'"1920x1080,auto"','GRUB_TERMINAL_OUTPUT':'"gfxterm"','GRUB_DISABLE_BOOTNEXT':'true','GRUB_DISABLE_SUBMENU':'true'}.items():
    line=key+'='+val
    if re.search(r'^'+key+'=',s,re.M):s=re.sub(r'^'+key+'=.*$',lambda m:line,s,flags=re.M)
    else:s+='\n'+line+'\n'
p.write_text(s)
PY
    if grub-mkconfig -o /boot/grub/grub.cfg.honor-new && grub-script-check /boot/grub/grub.cfg.honor-new; then
        mv /boot/grub/grub.cfg.honor-new /boot/grub/grub.cfg
    else
        cp -a "$backup/files/etc/default/grub" /etc/default/grub
        if [[ -e "$backup/files/etc/grub.d/29_honor_windows" ]]; then
            cp -a "$backup/files/etc/grub.d/29_honor_windows" /etc/grub.d/29_honor_windows
        else
            rm -f /etc/grub.d/29_honor_windows
        fi
        echo "Ошибка GRUB; прежнее меню сохранено. Резервная копия: $backup" >&2; exit 1
    fi
else
    echo 'Тема GRUB скопирована. Действующий GRUB не найден; установка загрузчика на диск не выполнялась.'
fi
if (( with_acpi )); then
    install -D -m644 "$repo_dir/hardware/acpi/SSDT27_TPD0.aml" /usr/lib/firmware/acpi/SSDT27_TPD0.aml
    install -D -m644 "$repo_dir/hardware/initcpio/acpi_override" /etc/initcpio/install/acpi_override
    python3 - <<'PY'
from pathlib import Path
import re
p=Path('/etc/mkinitcpio.conf');s=p.read_text();m=re.search(r'^HOOKS=\((.*?)\)',s,re.M|re.S)
if not m:raise SystemExit('Не найден HOOKS в mkinitcpio.conf; добавьте acpi_override вручную.')
hooks=m.group(1).split()
if 'acpi_override' not in hooks:
    hooks.insert(hooks.index('autodetect')+1 if 'autodetect' in hooks else 1,'acpi_override')
    s=s[:m.start()]+'HOOKS=('+' '.join(hooks)+')'+s[m.end():]
    p.write_text(s)
PY
    mkinitcpio -P
fi
# Ignore only the bogus keyboard collection of the FocalTech touchscreen.
install -D -m644 "$repo_dir/hardware/udev/99-honor-focaltech-phantom-mic.rules" /etc/udev/rules.d/99-honor-focaltech-phantom-mic.rules
udevadm control --reload-rules
systemctl enable sddm.service
systemctl enable --now NetworkManager.service bluetooth.service power-profiles-daemon.service
alsactl store
systemctl start alsa-restore.service
printf 'Готово. Резервная копия системы: %s\nТекущая графическая сессия не перезапускалась.\n' "$backup"
