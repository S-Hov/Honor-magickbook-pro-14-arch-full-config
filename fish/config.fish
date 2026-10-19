fish_add_path --global $HOME/.local/bin

if status is-interactive
    # Интерактивные настройки Fish
end


# Единый пакетный интерфейс: Shelly по умолчанию, выбор менеджера флагом.
source (status dirname)/functions/pac.fish

# micro вместо nano
function nano
    if command -q micro
        command micro $argv
    else
        command nano $argv
    end
end

alias yz="yazi"

alias update-grub="sudo grub-mkconfig -o /boot/grub/grub.cfg"

alias docker-start="sudo systemctl start docker.service"
alias docker-stop="sudo systemctl stop docker.service"
alias docker-status="systemctl status docker.service"

alias agy="antigravity-ide"


alias zed="zeditor"
