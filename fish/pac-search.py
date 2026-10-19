#!/usr/bin/env python3
"""Compact, read-only package search. All arguments go directly to the selected CLI."""
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys


def search(manager, source, query):
    if manager == 'shelly':
        cmd = [manager, 'search', source, *query, '--json']
        if source == 'standard':
            cmd += ['--limit', '1000000']
    else:
        cmd = [manager, '-Ss', '--color=never']
        if manager != 'pacman':
            cmd.append('--repo' if source == 'standard' else '--aur')
        cmd += ['--', *query]
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=40, env=dict(os.environ, LC_ALL='C'))
    # pacman/yay return 1 for an empty search, without an error message.
    if result.returncode and (result.stderr.strip() or result.stdout.strip()):
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    if result.returncode not in (0, 1):
        raise RuntimeError(f'код завершения {result.returncode}')
    if manager == 'shelly':
        rows = json.loads(result.stdout or '[]')
        if not isinstance(rows, list):
            raise ValueError('неожиданный формат JSON')
        return [(r['Name'], r.get('Version', ''), r.get('Repository') or ('aur' if source == 'aur' else 'repo'),
                 r.get('Description') or '', r.get('DownloadSize') if source == 'standard' else None) for r in rows]
    rows = []
    for line in result.stdout.splitlines():
        header = re.match(r'^(\S+)/(\S+)\s+(\S+)', line)
        if header:
            repo, name, version = header.groups()
            rows.append((name, version, repo, '', None))
        elif line[:1].isspace() and rows:
            last = rows[-1]
            rows[-1] = (*last[:3], (last[3] + ' ' + line.strip()).strip(), last[4])
    return rows


def download_sizes(rows):
    """Enrich only displayed official packages using the local pacman databases."""
    names = [f'{r[2]}/{r[0]}' for r in rows if r[2] != 'aur' and r[4] is None]
    if not names:
        return {}
    try:
        result = subprocess.run(['pacman', '-Si', '--', *names], text=True, capture_output=True,
                                timeout=10, env=dict(os.environ, LC_ALL='C'))
    except (OSError, subprocess.TimeoutExpired):
        return {}
    sizes = {}
    for block in result.stdout.strip().split('\n\n'):
        fields = dict(re.findall(r'^([^:\n]+?)\s*:\s*(.*)$', block, re.M))
        if all(k in fields for k in ('Repository', 'Name', 'Download Size')):
            sizes[(fields['Repository'], fields['Name'])] = fields['Download Size']
    return sizes


def short(text, width):
    text = ' '.join(str(text).split())
    return text if len(text) <= width else text[:width - 1] + '…'


def byte_size(value):
    if value is None:
        return '—'
    size = float(value)
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if size < 1024 or unit == 'TiB':
            return f'{size:.1f} {unit}'
        size /= 1024


def table(rows):
    if not rows:
        return
    sizes = download_sizes(rows)
    data = [(name, version or '—', source,
             byte_size(size) if size is not None else sizes.get((source, name), '—'), description or '—')
            for name, version, source, description, size in rows]
    headers = ('Пакет', 'Версия', 'Источник', 'Размер', 'Описание')
    widths = [max(len(headers[i]), *(len(row[i]) for row in data)) for i in range(4)]
    description_width = max(18, min(56, shutil.get_terminal_size((120, 24)).columns - sum(widths) - 16))
    widths.append(description_width)
    def border(left, middle, right):
        return left + middle.join('─' * (w + 2) for w in widths) + right
    def row(values):
        return '│ ' + ' │ '.join(short(v, w).ljust(w) for v, w in zip(values, widths)) + ' │'
    print(border('┌', '┬', '┐'))
    print(row(headers))
    print(border('├', '┼', '┤'))
    for values in data:
        print(row(values))
    print(border('└', '┴', '┘'))


def main():
    manager, *query = sys.argv[1:]
    show_all = '--all' in query
    query = [q for q in query if q != '--all']
    if not query or any(q.startswith('-') for q in query):
        print('Использование: pac [-менеджер] search [--all] <запрос>', file=sys.stderr)
        return 2
    sources = ['standard'] if manager == 'pacman' else ['standard', 'aur']
    rows, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [(s, pool.submit(search, manager, s, query)) for s in sources]
        for source, future in futures:
            try:
                rows.extend(future.result())
            except (RuntimeError, ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
                # Keep diagnostics short; report partial results explicitly.
                errors.append(f'{source}: {str(error).splitlines()[0][:220]}')
    rows = list(dict.fromkeys(rows))
    terms = [q.casefold() for q in query]
    rows.sort(key=lambda r: (0 if r[0].casefold() in terms else 1 if any(r[0].casefold().startswith(q) for q in terms) else 2, r[2] == 'aur', r[0]))
    visible = rows if show_all else rows[:25]
    table(visible)
    print(f'Получено: {len(rows)}. Показано: {len(visible)}.' + (' Полный список: pac search --all <запрос>.' if len(visible) < len(rows) else ''))
    if manager == 'shelly' and sum(r[2] == 'aur' for r in rows) >= 100:
        print('Shelly может ограничивать выдачу AUR. Для полного поиска уточните запрос или используйте pac -yay search --all <запрос>.')
    if any(r[2] == 'aur' for r in visible):
        print('AUR: размер скачивания заранее неизвестен (—).')
    for error in errors:
        print(f'Поиск неполный ({manager}): {error}', file=sys.stderr)
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
