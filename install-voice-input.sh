#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
(( EUID != 0 )) || { echo 'Запускайте обычным пользователем, без sudo.' >&2; exit 1; }
sudo pacman -S --needed openvino-intel-npu-plugin python-openvino python wl-clipboard pipewire libnotify acl
sudo usermod -aG render "$USER"
sudo install -Dm644 "$repo_dir/voice-input/70-honor-dictation-uinput.rules" /etc/udev/rules.d/70-honor-dictation-uinput.rules
sudo install -Dm644 "$repo_dir/voice-input/honor-dictation.conf" /etc/modules-load.d/honor-dictation.conf
sudo modprobe uinput
sudo udevadm control --reload-rules
sudo udevadm trigger /sys/class/misc/uinput
sudo setfacl -m "u:$USER:rw" /dev/uinput
# Give this session access immediately; future logins inherit the render group.
[[ ! -e /dev/accel/accel0 ]] || sudo setfacl -m "u:$USER:rw" /dev/accel/accel0
runtime="$HOME/.local/share/honor-dictation"
install -d "$runtime" "$HOME/.local/bin" "$HOME/.config/systemd/user"
python -m venv "$runtime/venv"
"$runtime/venv/bin/pip" install -r "$repo_dir/voice-input/requirements.txt"
python "$repo_dir/voice-input/download-model.py"
install -m644 "$repo_dir/voice-input/dictation.py" "$runtime/dictation.py"
install -m755 "$repo_dir/voice-input/honor-dictation" "$HOME/.local/bin/honor-dictation"
install -m644 "$repo_dir/voice-input/honor-dictation.service" "$HOME/.config/systemd/user/honor-dictation.service"
systemctl --user daemon-reload
systemctl --user restart honor-dictation.service
printf '\nГотово. Super+Ctrl+R: начать/закончить. Super+Ctrl+Esc: отменить.\nИспользуется текущий системный микрофон; в Niri нужен конфиг из этой сборки.\n'
