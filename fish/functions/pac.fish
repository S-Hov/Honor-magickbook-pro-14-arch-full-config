set -g __honor_pac_search (status dirname)/../pac-search.py

function pac --description "Единый интерфейс для Shelly, paru, yay и pacman"
    set -l helper shelly
    if contains -- "$argv[1]" -shelly -yay -paru -pacman
        set helper (string sub -s 2 -- $argv[1])
        set -e argv[1]
    end
    if test (count $argv) -eq 0; or contains -- "$argv[1]" help h --help -h
        __pac_help $helper
        return 0
    end
    if not command -q $helper
        echo "Менеджер $helper не установлен. Выберите -shelly, -yay, -paru или -pacman." >&2
        return 127
    end

    set -l action $argv[1]
    set -e argv[1]

    switch $action
        case install add i
            if test (count $argv) -eq 0
                echo "Использование: pac install <пакет...>"
                return 1
            end

            if test $helper = shelly
                # Bare queries search both official repositories and the AUR,
                # then let Shelly resolve and confirm the package to install.
                command shelly $argv
            else if test $helper = pacman
                command sudo pacman -S --needed $argv
            else
                command $helper -S --needed $argv
            end

        case remove rm delete
            if test (count $argv) -eq 0
                echo "Использование: pac remove <пакет...>"
                return 1
            end

            # Удаляет пакет, но не удаляет автоматически
            # все его зависимости и конфигурацию.
            if test $helper = shelly
                command shelly remove standard $argv
            else if test $helper = pacman
                command sudo pacman -R $argv
            else
                command $helper -R $argv
            end

        case purge uninstall
            if test (count $argv) -eq 0
                echo "Использование: pac purge <пакет...>"
                return 1
            end

            # Удаляет пакет, неиспользуемые зависимости
            # и системные конфигурационные файлы.
            if test $helper = shelly
                command shelly remove standard --cascade --remove-config $argv
            else if test $helper = pacman
                command sudo pacman -Rns $argv
            else
                command $helper -Rns $argv
            end

        case search find s
            if test (count $argv) -eq 0
                echo "Использование: pac search <запрос>"
                return 1
            end

            command python3 $__honor_pac_search $helper $argv

        case list ls installed
            # Без аргументов выводит все установленные пакеты.
            # С аргументами ищет среди установленных пакетов.
            if test (count $argv) -eq 0
                command pacman -Q
            else
                command pacman -Qs $argv
            end

        case info show
            if test (count $argv) -eq 0
                echo "Использование: pac info <пакет...>"
                return 1
            end

            if test $helper = shelly
                # pacman handles repository metadata; fall back to AUR metadata.
                command pacman -Si $argv
                or command shelly search aur --detail $argv
            else
                command $helper -Si $argv
            end

        case local-info installed-info
            if test (count $argv) -eq 0
                echo "Использование: pac local-info <пакет...>"
                return 1
            end

            command pacman -Qi $argv

        case update upgrade up
            # В Arch update и upgrade фактически являются
            # одной операцией полного обновления системы.
            if test $helper = shelly
                command shelly upgrade all
            else if test $helper = pacman
                command sudo pacman -Syu
            else
                command $helper -Syu
            end

        case refresh
            # Принудительно обновляет базы пакетов и систему.
            # Обычно достаточно обычного pac update.
            if test $helper = shelly
                command shelly sync standard
                and command shelly upgrade all
            else if test $helper = pacman
                command sudo pacman -Syyu
            else
                command $helper -Syyu
            end

        case orphan orphans
            # Показывает зависимости, которые больше
            # не требуются ни одному установленному пакету.
            command pacman -Qdtq

        case remove-orphans autoremove
            set -l orphans (command pacman -Qdtq)

            if test (count $orphans) -eq 0
                echo "Неиспользуемые зависимости не найдены."
                return 0
            end

            echo "Будут удалены неиспользуемые зависимости:"
            printf "  %s\n" $orphans

            read --prompt-str="Продолжить? [y/N] " -l confirmation

            switch (string lower -- $confirmation)
                case y yes д да
                    command sudo pacman -Rns $orphans
                case '*'
                    echo "Отменено."
            end

        case clean
            # Безопасная очистка старых пакетов.
            # Не используется -Scc, чтобы не удалять весь кэш.
            command sudo pacman -Sc

        case download
            if test (count $argv) -eq 0
                echo "Использование: pac download <пакет...>"
                return 1
            end

            if test $helper = shelly
                command sudo pacman -Sw $argv
            else if test $helper = pacman
                command sudo pacman -Sw $argv
            else
                command $helper -Sw $argv
            end

        case help h --help -h
            __pac_help $helper

        case raw
            # Передаёт аргументы напрямую выбранному менеджеру.
            if test $helper = shelly
                command shelly $argv
            else if test $helper = pacman
                command sudo pacman $argv
            else
                command $helper $argv
            end

        case '*'
            echo "Неизвестная команда: $action"
            echo
            __pac_help $helper
            return 1
    end
end


function __pac_help --argument-names helper
    printf 'Менеджер: %s (по умолчанию Shelly)\n' $helper
    printf '%s\n' 'pac [-shelly|-yay|-paru|-pacman] <команда> [пакеты]' '' \
        'install / remove / purge       Установка / удаление / удаление с зависимостями' \
        'search [--all] <запрос>        Таблица пакетов, по умолчанию до 25 результатов' \
        'info / local-info <пакет>      Подробности о пакете' \
        'list [запрос]                 Установленные пакеты' \
        'update / refresh              Обновить систему / принудительно обновить базы' \
        'orphan / remove-orphans       Найти / удалить лишние зависимости' \
        'clean / download / raw        Очистить кэш / скачать / исходные аргументы' '' \
        'pac search firefox' 'pac -pacman search firefox' 'pac -yay install brave-bin' \
        'pac -shelly update' 'pac search --all browser' '' \
        'pacman ищет только в официальных репозиториях; остальные также в AUR.' \
        'Локальная база, сироты и очистка кэша обслуживаются pacman.'
end
