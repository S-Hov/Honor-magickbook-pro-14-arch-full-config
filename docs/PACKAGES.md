# Программы

`packages/official.txt` и `packages/aur.txt` — списки, используемые установщиком.
Noctalia v5 берётся из официального репозитория, Brave/cliamp/Shelly — из AUR.
Не все пакеты из прежней системы нужны новой: Lenovo cooling, NVIDIA-инструменты
и локальные модели Ollama исключены.

`packages/installed-explicit.txt` и `packages/installed-foreign.txt` — справочный
снимок текущей системы. Установщик их не выполняет: там могут быть приложения
из дополнительных репозиториев и AUR, требующие отдельной установки.

Профили VPN, настройки подключений и входы в аккаунты не входят в набор.
Docker и Antigravity встречаются в личных Fish alias, но не устанавливаются
автоматически. Их можно установить отдельно, если они нужны.

В Zed сохранены auto_install_extensions: темы/иконки, Biome, Codebook, Emmet,
HTML, SCSS, Prisma и Dockerfile. Zed скачает расширения при первом запуске.
Модели и интеграции Ollama отключены. Для запуска редактора в Arch используется
`zeditor`; в Fish предусмотрен alias `zed`.
