#!/usr/bin/env python3
"""Build Apple-Sumi-Red from the included GPL-3.0 SVG source."""
from pathlib import Path
import argparse, shutil, subprocess, tempfile

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bitmaps', type=Path, help='Keep rendered 256px source bitmaps here')
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='apple-sumi-red-') as temp:
    bitmaps = args.bitmaps.resolve() if args.bitmaps else Path(temp)/'bitmaps'
    subprocess.run(['node', str(ROOT/'render.cjs'), str(bitmaps)], check=True)
    subprocess.run(['ctgen', str(ROOT/'x.build.toml'), '-p', 'x11',
                    '-d', str(bitmaps), '-o', str(Path(temp)/'themes'),
                    '-n', 'Apple-Sumi-Red', '-c', 'Apple cursors in the Sumi Red palette'], check=True)
    theme = Path(temp)/'themes/Apple-Sumi-Red'
    shutil.copy2(ROOT/'LICENSE', theme/'LICENSE')
    index = theme/'index.theme'
    index.write_text('[Icon Theme]\nName=Apple-Sumi-Red\n'
                     'Comment=Apple cursors in the Sumi Red palette\nInherits=Adwaita\n')
    target = ROOT.parent/'Apple-Sumi-Red'
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(theme, target, symlinks=True)
    print('Built:', target)
