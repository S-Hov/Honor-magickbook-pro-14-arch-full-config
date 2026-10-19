# Конфигурация Kitty

Настройки терминала Kitty для Wayland/Niri: Fish как shell, Hack Nerd Font, небольшая прозрачность, cursor trail и палитра Noctalia.

## Файлы

| Файл | Что делает |
| --- | --- |
| `kitty.conf` | Основные настройки терминала и подключение темы |
| `themes/noctalia.conf` | Активная цветовая палитра Noctalia |
| `current-theme.conf` | Сохранённая стандартная тема Kitty; оставлена как быстрый fallback |

## Зависимости

```bash
sudo pacman -S --needed kitty fish ttf-hack-nerd
```

## Установка

```bash
mkdir -p ~/.config/kitty
cp -a ./kitty/. ~/.config/kitty/
```

## Что настроено

- семейство `Hack Nerd Font` и размер 13 pt;
- Fish как оболочка;
- opacity `0.98`;
- beam cursor с коротким cursor trail;
- внутренний отступ 22 pt;
- закрытие окна без дополнительного подтверждения;
- тема из `themes/noctalia.conf`.

Чтобы вернуться к стандартной теме, замените в `kitty.conf`:

```text
include themes/noctalia.conf
```

на:

```text
include current-theme.conf
```

## Проверка

```bash
kitty +kitten choose-fonts
kitty --debug-config
```

Если Kitty не находит шрифт, выберите установленное семейство через `choose-fonts` и обновите `font_family`. Конфиг можно перечитать в запущенном Kitty сочетанием `Ctrl+Shift+F5`.
