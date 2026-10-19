#!/usr/bin/env python3
"""Restore portable dotfiles; --dry-run validates without changing the account."""
from pathlib import Path
import argparse, datetime, json, os, shutil, subprocess, tempfile, tomllib

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', HOME / '.config'))
DATA = Path(os.environ.get('XDG_DATA_HOME', HOME / '.local/share'))
STATE = Path(os.environ.get('XDG_STATE_HOME', HOME / '.local/state'))
APPS = 'niri fish kitty noctalia gtk-3.0 gtk-4.0 btop helix yazi qt5ct qt6ct micro telegram-desktop'.split()
TARGETS = {name: CONFIG / name for name in APPS}
TARGETS.update({'zed/config': CONFIG/'zed', 'zed/codebook': CONFIG/'codebook',
               'wallpapers': HOME/'Pictures/wallpapers', 'color-schemes': DATA/'color-schemes',
               'codex/themes': Path(os.environ.get('CODEX_HOME', HOME/'.codex'))/'themes',
               'brave-flags.conf': CONFIG/'brave-flags.conf',
               'noctalia-state/settings.toml': STATE/'noctalia/settings.toml'})

def render(source, target):
    if source.is_dir():
        shutil.copytree(source, target, ignore=shutil.ignore_patterns('README.md', '*.log', '*.lock'))
        files = list(target.rglob('*'))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        files = [target]
    for p in files:
        if not p.is_file(): continue
        try: text = p.read_text()
        except UnicodeDecodeError: continue
        if '@@HOME@@' in text: p.write_text(text.replace('@@HOME@@', str(HOME)))

def validate(stage):
    for p in stage.rglob('*.toml'): tomllib.loads(p.read_text())
    checks = [('niri', ['validate', '-c', str(stage/'niri/config.kdl')]),
              ('fish', ['-n', str(stage/'fish/config.fish')]),
              ('noctalia', ['config', 'validate', str(stage/'noctalia/config.toml')])]
    for command, args in checks:
        if shutil.which(command): subprocess.run([command, *args], check=True)
        else: print(f'{command}: не установлен, проверка пропущена')

def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir(): shutil.copytree(source, target, dirs_exist_ok=True)
    else: shutil.copy2(source, target)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', type=Path, metavar='BACKUP')
    args = parser.parse_args()
    if os.geteuid() == 0: parser.error('Запускайте от обычного пользователя, без sudo.')
    if args.rollback:
        backup = args.rollback.resolve()
        manifest = json.loads((backup/'manifest.json').read_text())
        allowed = {str(p) for p in TARGETS.values()} | {str(CONFIG/'mimeapps.list')}
        for entry in manifest:
            target = Path(entry['target'])
            if str(target) not in allowed: raise ValueError(f'Недопустимый путь: {target}')
            if target.is_dir() and not target.is_symlink(): shutil.rmtree(target)
            elif target.exists() or target.is_symlink(): target.unlink()
            if entry['existed']: copy(backup/entry['backup'], target)
        if (backup/'interface.dconf').exists() and shutil.which('dconf'):
            subprocess.run(bus_command(['dconf','load','/org/gnome/desktop/interface/']),
                           input=(backup/'interface.dconf').read_bytes(), check=True)
        print('Пользовательские настройки восстановлены из', backup)
        return
    with tempfile.TemporaryDirectory(prefix='honor-config-') as temp:
        stage = Path(temp)
        for name in TARGETS: render(ROOT/name, stage/name)
        validate(stage)
        if args.dry_run:
            print('Dry run: конфиги проверены; файлы пользователя не изменены.')
            return
        backup = STATE/'honor-magicbook-config-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup.mkdir(parents=True)
        manifest = []
        for i, target in enumerate([*TARGETS.values(), CONFIG/'mimeapps.list']):
            entry = {'target':str(target), 'existed':target.exists(), 'backup':str(i)}
            if entry['existed']: copy(target, backup/str(i))
            manifest.append(entry)
        (backup/'manifest.json').write_text(json.dumps(manifest, indent=2))
        if shutil.which('dconf'):
            result = subprocess.run(['dconf','dump','/org/gnome/desktop/interface/'], capture_output=True, check=True)
            (backup/'interface.dconf').write_bytes(result.stdout)
        for name, target in TARGETS.items():
            if name == 'niri':
                copy(stage/name/'cfg', target/'cfg')
                copy(stage/name/'config.kdl', target/'config.kdl')
            else: copy(stage/name, target)
        if shutil.which('dconf'):
            subprocess.run(bus_command(['dconf','load','/org/gnome/desktop/interface/']),
                           input=(ROOT/'desktop-interface.ini').read_bytes(), check=True)
        if Path('/usr/share/applications/brave-browser.desktop').exists():
            subprocess.run(['xdg-settings','set','default-web-browser','brave-browser.desktop'], check=True)
            for mime in ['text/html','application/xhtml+xml','x-scheme-handler/http','x-scheme-handler/https']:
                subprocess.run(['xdg-mime','default','brave-browser.desktop',mime], check=True)
        else: print('Brave не установлен: сначала выполните install-packages.sh, затем restore.sh.')
        if shutil.which('noctalia'):
            subprocess.run(['noctalia','msg','config-reload'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print('Установлено. Резервная копия:', backup)
        print('Откат: ./restore.sh --rollback', backup)

def bus_command(command):
    return command if os.environ.get('DBUS_SESSION_BUS_ADDRESS') else ['dbus-run-session','--',*command]

if __name__ == '__main__': main()
