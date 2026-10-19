# Оборудование и границы переноса

| Узел | Действующее решение |
| --- | --- |
| CPU / GPU | Intel Panther Lake, xe, Mesa, vulkan-intel, intel-media-driver |
| Экран | eDP-1, 3120×2080 @ 120 Гц, Niri scale 2 |
| Wi-Fi | Intel AX211, iwlwifi + linux-firmware + wireless-regdb, NetworkManager |
| Звук | Realtek ALC256, SOF Intel PTL, sof-firmware, ALSA UCM, PipeWire + WirePlumber |
| Микрофон | Встроенный четырёхканальный DMIC через SOF |
| Bluetooth | btintel_pcie + BlueZ |
| Камера | USB Shinetech 3277:00de, UVC/V4L2 |
| Яркость | intel_backlight, brightnessctl / Noctalia |
| Питание | power-profiles-daemon, профиль balanced |
| Ввод | Встроенная клавиатура работает; тачпад восстановлен ACPI override |

Рецепты Lenovo Legion, вентиляторы, EC-кривые, NVIDIA и AMD GPU сюда не перенесены.
Параметры разметки диска, UUID, fstab и пароли не заменяются установщиком.

## ACPI

`hardware/acpi/SSDT27_TPD0.aml` — именно работавшая на этом ноутбуке таблица.
Её паспорт и SHA256 находятся в `hardware/machine.json`.
Назначение mkinitcpio hook — поместить AML в **early uncompressed CPIO**.
Простое добавление файла в сжатую часть initramfs не эквивалентно этому механизму.

Применять только на HONOR ZQC-P, product_version M1230, BIOS 1.10.
Готовая таблица не является универсальным патчем семейства MagicBook.
При смене BIOS сначала проверьте, исправлена ли проблема изготовителем.

После установки с --acpi и перезагрузки:

```bash
journalctl -b -k | rg 'Table Upgrade|I2C_DEVT|Touchpad'
sudo lsinitcpio --early /boot/initramfs-linux.img | rg 'kernel/firmware/acpi/'
```

Клавиатура на момент экспорта работает без дополнительных i8042-параметров;
необходимости добавлять их на этой установке не установлено.

## Звук

Причиной отсутствия аудиоустройств был недостающий WirePlumber/аудиостек.
Для динамиков хватило корректного маршрута и громкости: на 35% сигнал был
слишком тихим, на 85% воспроизведение подтверждено. Патчи кодека и принудительное
отключение SOF не применялись. Установщик сохраняет текущее ALSA state.
Громкость пользователя хранится в WirePlumber, его runtime-state намеренно
не экспортирован. На новой установке при необходимости:

```bash
wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.85
pw-play /usr/share/sounds/alsa/Front_Left.wav
```

## Что требует физической проверки

Сон/пробуждение, отпечаток пальца, Bluetooth-периферия и гарнитурный микрофон.
Включённый контроллер Bluetooth не означает проверку каждого устройства.

## Самопроизвольное переключение микрофона: FocalTech UNKNOWN

18 октября 2026 найдена причина: вспомогательное устройство
`FTSC1000:00 2808:5662 UNKNOWN` объявляет только KEY_MICMUTE (248), держит
клавишу нажатой и выдаёт EV_KEY value=2 примерно 29 раз в секунду.
Из-за повтора привязки Niri постоянно запускалась `noctalia msg mic-mute`.
Это отдельная HID-коллекция сенсорного экрана, не основная клавиатура.

Исправление:

- `repeat=false` для XF86AudioMicMute и XF86AudioMute в Niri.
- Точное правило `hardware/udev/99-honor-focaltech-phantom-mic.rules` задаёт
  `LIBINPUT_IGNORE_DEVICE=1` только коллекции с именем `FTSC1000:00 2808:5662 UNKNOWN`.
- Основной touchscreen `FTSC1000:00 2808:5662`, клавиатура и Huawei WMI остаются активны.

Правило устанавливает `install-system.sh`; после восстановления применится
при следующем добавлении устройства или перезагрузке. На текущей системе
вспомогательный узел адресно переобъявлен через udev, сессия не перезапускалась.
Проверено: Niri больше не открывает ложный узел, настоящий touchscreen остаётся
открыт; новые серии команд mute прекратились, состояние микрофона стабильно.
Микрофон оставлен выключенным, как было до исправления.

При устранении ошибки в будущем ядре/прошивке правило можно удалить из
`/etc/udev/rules.d/` и перезагрузить систему. Это обход ошибочного ввода,
а не замена драйвера сенсорного экрана.

Механизм: [официальная документация libinput](https://wayland.freedesktop.org/libinput/doc/latest/device-configuration-via-udev.html).
