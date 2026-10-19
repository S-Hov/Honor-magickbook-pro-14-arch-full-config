# Откат и запасной вход

## Пользовательские настройки

Путь резервной копии печатает restore.sh. Используйте её для того же пользователя:

```bash
./restore.sh --rollback ~/.local/state/honor-magicbook-config-backups/ИМЯ-КОПИИ
```

Откат заменяет только перечисленные в manifest.json каталоги/файлы конфигов и
схемы оформления. Установленные pacman-пакеты не удаляются.

## Если новый SDDM не открывается

Перейдите на TTY (`Ctrl+Alt+F3`), войдите обычным пользователем и отключите тему:

```bash
sudo mv /etc/sddm.conf.d/90-sumi-red.conf /etc/sddm.conf.d/90-sumi-red.conf.disabled
sudo systemctl restart sddm
```

Перезапуск SDDM завершает действующие графические сессии — делайте это из TTY
после сохранения работы. Для постоянного терминального входа:

```bash
sudo systemctl disable sddm
```

После следующей загрузки войдите в TTY и выполните `niri-session`.
Это вариант с паролем в терминале, автоматический вход не включается.

## Вернуть прежнее меню GRUB

```bash
system_backup=$(cat /var/backups/arch-honor-config-last)
sudo cp -a "$system_backup/files/etc/default/grub" /etc/default/grub
sudo cp -a "$system_backup/files/boot/grub/grub.cfg" /boot/grub/grub.cfg
sudo grub-script-check /boot/grub/grub.cfg
```

Установка пакетов не откатывается этими командами. Каталоги тем могут остаться
на диске: без ссылок на них они не активны.

## Ошибка после изменения ACPI

Из TTY или Arch live USB восстановите из той же системной копии
`/etc/mkinitcpio.conf`, hook и AML, если они существовали до установки.
Если их раньше не было — удалите только добавленные этим набором hook/AML и
уберите acpi_override из HOOKS. Затем выполните `sudo mkinitcpio -P`.
На этой модели возврат к исходной прошивке может снова отключить тачпад;
подготовьте внешнюю мышь. Самостоятельно переносить AML другого BIOS нельзя.
