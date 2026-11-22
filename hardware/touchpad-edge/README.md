# HID-BPF для Goodix TOPS0102

Объект `honor-tops0102-edge.bpf.o` совпадает с проверенным на HONOR ZQC-P
M1230 под Arch Linux `7.3.4-arch1-2`. Исходник сохранён под GPL-2.0-only.
[Исходная реализация HONOR_ZQC-P_M1010](https://github.com/rs0x29a/Linux-on-HONOR-MagicBook-14-Pro-2026-AI_ZQC-P_M1010/blob/95631852eeda83b8a32a4913f5431475daad3ca1/patch/touchpad-edge/zqc-p/M1010/honor-tops0102-edge.bpf.c).

## Пересборка

Для сборки использованы `clang`, `bpftool` (пакет `bpf` в Arch), заголовки
`libbpf` и BTF работающего ядра. Команды из этого каталога:

```bash
build_dir=$(mktemp -d)
headers=https://raw.githubusercontent.com/gregkh/linux/v7.3.4/drivers/hid/bpf/progs
for header in hid_bpf.h hid_bpf_helpers.h hid_report_descriptor_helpers.h; do
    curl -fsSL "$headers/$header" -o "$build_dir/$header" || exit 1
done
bpftool btf dump file /sys/kernel/btf/vmlinux format c > "$build_dir/vmlinux.h"
clang -O2 -g -target bpf -mcpu=v3 -D__TARGET_ARCH_x86 -I"$build_dir" \
    -c honor-tops0102-edge.bpf.c -o "$build_dir/honor-tops0102-edge.bpf.o"
udev-hid-bpf inspect "$build_dir/honor-tops0102-edge.bpf.o"
```

При сборке под другое ядро используйте его BTF и тег исходников.
