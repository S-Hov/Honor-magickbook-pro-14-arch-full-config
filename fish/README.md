# Конфигурация Fish

Интерактивная оболочка Fish с Fisher, prompt Tide и пользовательской обёрткой `pac` для управления пакетами Arch Linux.

## Файлы

| Файл/каталог | Что делает |
| --- | --- |
| `config.fish` | Пользовательские функции `pac`, `nano` и alias `yz` |
| `fish_plugins` | Список плагинов Fisher: Fisher и Tide v6 |
| `fish_variables` | Universal variables Fish и настройки prompt Tide |
| `functions/` | Функции Fisher/Tide и генерация prompt |
| `completions/` | Автодополнение Fisher/Tide |
| `conf.d/` | Инициализация Tide |

Большая часть файлов в `functions/`, `completions/` и `conf.d/` сгенерирована плагинами. Пользовательскую логику лучше добавлять в `config.fish` или отдельные собственные файлы в `functions/`.

## Зависимости

```bash
sudo pacman -S --needed fish micro git
```

Опционально установите `paru` или `yay`; функция `pac` выберет их автоматически, иначе использует обычный `pacman`.

## Установка

```bash
mkdir -p ~/.config/fish
cp -a ./fish/. ~/.config/fish/
```

При необходимости обновите плагины:

```fish
fisher update
```

## Команда `pac`

Примеры:

```fish
pac install firefox
pac search browser
pac list
pac info niri
pac update
pac remove firefox
pac purge firefox
pac orphan
pac remove-orphans
pac clean
pac help
```

`remove` выполняет обычное удаление, а `purge` также удаляет неиспользуемые зависимости и системные конфигурационные файлы пакета. `remove-orphans` запрашивает подтверждение перед удалением.

Дополнительно:

- команда `nano` открывает Micro, если он установлен, и иначе запускает настоящий Nano;
- `yz` — короткий alias для запуска Yazi;
- `$EDITOR` сохранён как `micro` в `fish_variables`.

## Проверка

```bash
fish -n ~/.config/fish/config.fish
fish -c 'type pac; type fisher; type tide'
```

Перед публикацией `fish_variables` проверяйте его на токены и приватные значения: universal variables могут сохраняться туда автоматически.
