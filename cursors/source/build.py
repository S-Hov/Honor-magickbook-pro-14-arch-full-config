#!/usr/bin/env python3
"""Build crisp, native-size Xcursors directly from the included SVG source."""
from pathlib import Path
import argparse, shutil, subprocess, tempfile, tomllib
from PIL import Image
from clickgen.cursors import CursorFrame, CursorImage
from clickgen.writer.x11 import to_x11

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bitmaps', type=Path, help='Keep native-size PNGs in size subdirectories here')
args = parser.parse_args()
config = tomllib.loads((ROOT/'x.build.toml').read_text())['cursors']
fallback = config['fallback_settings']
sizes = fallback['x11_sizes']
with tempfile.TemporaryDirectory(prefix='apple-sumi-red-') as temp:
    bitmaps = args.bitmaps.resolve() if args.bitmaps else Path(temp)/'bitmaps'
    # 256px is only for the gallery; Xcursor files use the final native sizes.
    render_sizes = sorted(set(sizes + [256]))
    subprocess.run(['node', str(ROOT/'render.cjs'), str(bitmaps),
                    ','.join(map(str, render_sizes))], check=True)
    theme = Path(temp)/'Apple-Sumi-Red'
    cursors = theme/'cursors'
    cursors.mkdir(parents=True)
    for key, entry in config.items():
        if key == 'fallback_settings':
            continue
        frames = []
        filenames = sorted(p.name for p in (bitmaps/'256').glob(entry['png']))
        if not filenames:
            raise FileNotFoundError(entry['png'])
        hx = entry.get('x_hotspot', fallback['x_hotspot'])
        hy = entry.get('y_hotspot', fallback['y_hotspot'])
        for filename in filenames:
            images = []
            for size in sizes:
                image = Image.open(bitmaps/str(size)/filename).convert('RGBA')
                assert image.size == (size, size)
                # Keep the original hotspot convention, scaled from the 256px viewBox.
                hotspot = (int(hx * size / 256), int(hy * size / 256))
                images.append(CursorImage(image=image, hotspot=hotspot, nominal=size))
            frames.append(CursorFrame(images, delay=entry.get('x11_delay', fallback['x11_delay'])))
        name = entry['x11_name']
        (cursors/name).write_bytes(to_x11(frames))
        for alias in entry.get('x11_symlinks', []):
            (cursors/alias).symlink_to(name)
    for filename in ['LICENSE', 'LICENSE-Bibata']:
        shutil.copy2(ROOT/filename, theme/filename)
    (theme/'index.theme').write_text('[Icon Theme]\nName=Apple-Sumi-Red\n'
        'Comment=Sumi Red: Bibata Modern pointer and Apple cursors, rendered at native sizes\n'
        'Inherits=Adwaita\n')
    (theme/'cursor.theme').write_text('[Icon Theme]\nName=Apple-Sumi-Red\nInherits=Apple-Sumi-Red\n')
    target = ROOT.parent/'Apple-Sumi-Red'
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(theme, target, symlinks=True)
    print('Built', len(config)-1, 'cursors at', len(sizes), 'native sizes:', target)
