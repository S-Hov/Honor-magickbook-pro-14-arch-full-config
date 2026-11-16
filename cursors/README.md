# Sumi Red / Bibata + Apple

Основной указатель — Bibata Modern, остальные курсоры — Apple, в палитре рабочего стола Honor: тёплый светлый `#E6E0D9`,
тёмная обводка `#090A0D`, красные акценты `#D95757` / `#9B454B`.
Цветные индикаторы ожидания перекрашены в красную гамму, анимации сохранены.
Мягкие SVG-тени отключены. Каждый размер рисуется напрямую из SVG, без
уменьшения промежуточного PNG. Включены 14 размеров от 16 до 96 px, в том числе 24 и 48 для масштаба 200%.

![Превью курсоров](preview.png)

`Apple-Sumi-Red/` — готовая Xcursor-тема для Niri/Wayland и X11/XWayland.
`restore.sh` устанавливает её в `~/.local/share/icons/`, настраивает курсор Niri,
GTK, dconf и пользовательскую тему по умолчанию. Размер — 24 логических пикселя.
Некоторые уже открытые приложения обновляют курсор только после перезапуска.

## Исходники и сборка

Основа: [ful1e5/apple_cursor](https://github.com/ful1e5/apple_cursor),
commit `fe044a42b4e9cea16ea762d2ed9004f6d7b35543`, лицензия GPL-3.0.
Основной указатель заменён на [Bibata Modern](https://github.com/ful1e5/Bibata_Cursor),
commit `ddb09273cde49faeb6a32282660ff4293f52d6e0`,
`svg/groups/modern/left_ptr.svg`, hotspot 55/17 на холсте 256px; GPL-3.0.
SVG, manifest с hotspots/алиасами и обе лицензии включены в `source/`.
Цвета и отключение теней выполняет `source/render.cjs`; сборку напрямую из PNG конечного размера — `source/build.py`.

Сборка не требует sudo, но нужны Node.js/npm, Python и venv:

```bash
cd cursors/source
npm ci --no-audit --no-fund
python -m venv .venv
.venv/bin/pip install -r requirements.txt
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python build.py
```

Чтобы сохранить растры конечных размеров и обновить галерею:

```bash
PATH="$PWD/.venv/bin:$PATH" .venv/bin/python build.py --bitmaps /tmp/sumi-red-bitmaps
.venv/bin/python preview.py /tmp/sumi-red-bitmaps
```

Для возврата Adwaita задайте `xcursor-theme "Adwaita"` в `niri/cfg/misc.kdl`,
`cursor-theme='Adwaita'` в `desktop-interface.ini` и соответствующие значения
в GTK settings.ini и `cursors/default/index.theme`, затем выполните restore.sh.
