#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
with_acpi=0
case "${1:-}" in
    '') ;;
    --acpi) with_acpi=1 ;;
    --dry-run) echo 'Установка: GRUB void-terminal, SDDM Qylock Orbital, NetworkManager, Bluetooth, PPD, ALSA, жест яркости Goodix. ACPI только с --acpi.'; exit 0 ;;
    *) echo 'Использование: sudo ./install-system.sh [--acpi]' >&2; exit 1 ;;
esac
(( EUID == 0 )) || { echo 'Нужен sudo.' >&2; exit 1; }
command -v udev-hid-bpf >/dev/null || {
    echo 'Нужен пакет udev-hid-bpf. Установите его через ./install-packages.sh.' >&2
    exit 1
}
edge_object=/etc/udev-hid-bpf/honor-tops0102-edge.bpf.o
edge_rule=/etc/udev/rules.d/99-hid-bpf-honor-tops0102-edge.rules
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
paths=(/etc/udev/rules.d/99-honor-focaltech-phantom-mic.rules /etc/grub.d/29_honor_windows /etc/default/grub /boot/grub/grub.cfg /etc/sddm.conf.d/90-sumi-red.conf /etc/sddm.conf.d/99-ryoku-orbital.conf /etc/mkinitcpio.conf /etc/initcpio/install/acpi_override /usr/lib/firmware/acpi/SSDT27_TPD0.aml)
paths+=("$edge_object" "$edge_rule")
for file in "${paths[@]}"; do
    if [[ -e "$file" ]]; then
        install -d "$backup/files$(dirname "$file")"
        cp -a "$file" "$backup/files$file"
    fi
done
printf '%s\n' "$backup" > /var/backups/arch-honor-config-last
install -d -m755 /boot/grub/themes /usr/share/sddm/themes /etc/sddm.conf.d
[[ ! -d /boot/grub/themes/void-terminal ]] || cp -a /boot/grub/themes/void-terminal "$backup/previous-void-terminal"
cp -a "$repo_dir/grub/void-terminal" /boot/grub/themes/
chown -R root:root /boot/grub/themes/void-terminal
chmod -R a+rX /boot/grub/themes/void-terminal
for theme in sumi-red ryoku-orbital; do
    theme_dir="/usr/share/sddm/themes/$theme"
    [[ ! -d "$theme_dir" ]] || cp -a "$theme_dir" "$backup/previous-$theme"
    cp -a "$repo_dir/sddm/$theme" /usr/share/sddm/themes/
    chown -R root:root "$theme_dir"
    chmod -R a+rX "$theme_dir"
done
install -m644 "$repo_dir/sddm/90-sumi-red.conf" /etc/sddm.conf.d/90-sumi-red.conf
install -m644 "$repo_dir/sddm/99-ryoku-orbital.conf" /etc/sddm.conf.d/99-ryoku-orbital.conf
if [[ -f /etc/default/grub && -f /boot/grub/grub.cfg ]]; then
    install -o root -g root -m755 "$repo_dir/grub/29_honor_windows" /etc/grub.d/29_honor_windows
    python3 - <<'PY'
from pathlib import Path
import re
p=Path('/etc/default/grub');s=p.read_text()
for key,val in {'GRUB_THEME':'"/boot/grub/themes/void-terminal/theme.txt"','GRUB_GFXMODE':'"1920x1080,auto"','GRUB_TERMINAL_OUTPUT':'"gfxterm"','GRUB_DISABLE_BOOTNEXT':'true','GRUB_DISABLE_SUBMENU':'true'}.items():
    line=key+'='+val
    if re.search(r'^'+key+'=',s,re.M):s=re.sub(r'^'+key+'=.*$',lambda m:line,s,flags=re.M)
    else:s+='\n'+line+'\n'
p.write_text(s)
PY
    if bash "$repo_dir/grub/void-terminal/install.sh"; then
        : # Theme installer validates and atomically activates the new config.
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
install -D -m644 "$repo_dir/hardware/touchpad-edge/${edge_object##*/}" "$edge_object"
install -D -m644 "$repo_dir/hardware/udev/${edge_rule##*/}" "$edge_rule"
udevadm control --reload-rules
# Attach to an already present touchpad without reprobe or duplicate handlers.
# If ACPI exposes it after reboot, the udev add rule handles it then.
for device in /sys/bus/hid/devices/0018:27C6:0F9A.*; do
    [[ -r "$device/modalias" ]] || continue
    [[ $(<"$device/modalias") == hid:b0018g0004v000027C6p00000F9A ]] || continue
    loaded=$(udev-hid-bpf list-loaded --syspath "$device")
    grep -Fq '"name": "honor_tops0102_edge"' <<< "$loaded" && continue
    udev-hid-bpf add "$device" "$edge_object"
    loaded=$(udev-hid-bpf list-loaded --syspath "$device")
    if ! grep -Fq '"name": "honor_tops0102_edge"' <<< "$loaded"; then
        echo "Не удалось загрузить HID-BPF для $device." >&2
        exit 1
    fi
done
systemctl enable sddm.service
systemctl enable --now NetworkManager.service bluetooth.service power-profiles-daemon.service
alsactl store
systemctl start alsa-restore.service
printf 'Готово. Резервная копия системы: %s\nТекущая графическая сессия не перезапускалась.\n' "$backup"
