#!/usr/bin/env bash
# Optional: fingerprint first, then the existing password authentication for sudo.
set -euo pipefail
(( EUID == 0 )) || { echo 'Запустите: sudo ./enable-sudo-fingerprint.sh' >&2; exit 1; }
[[ -f /usr/lib/security/pam_fprintd.so ]] || { echo 'Сначала установите fprintd.' >&2; exit 1; }
python3 - <<'PY'
from pathlib import Path
import datetime, shutil, os
p=Path('/etc/pam.d/sudo');s=p.read_text()
if 'pam_fprintd.so' in s:
    raise SystemExit('В sudo уже настроен pam_fprintd; существующая настройка сохранена.')
if not any(line.split()[:3] == ['auth', 'include', 'system-auth'] for line in s.splitlines()):
    raise SystemExit('Необычный PAM-конфиг sudo; требуется ручная проверка.')
b=Path('/var/backups')/('honor-sudo-fingerprint-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
b.mkdir(mode=0o700);shutil.copy2(p,b/'sudo')
lines=s.splitlines(keepends=True)
i=next(i for i,line in enumerate(lines) if line.split()[:1] == ['auth'])
lines.insert(i, 'auth        sufficient    pam_fprintd.so max-tries=1 timeout=10\n')
new=p.with_name('sudo.honor-new');shutil.copy2(p,new);new.write_text(''.join(lines));os.replace(new,p)
print('Готово: sudo ожидает отпечаток до 10 секунд, затем предлагает пароль.')
print('Резервная копия:',b/'sudo')
PY
