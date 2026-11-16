#!/usr/bin/env python3
"""Render a gallery from the actual recolored source bitmaps."""
from pathlib import Path
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont
root = Path(__file__).resolve().parent
bitmaps = Path(sys.argv[1])/'96'
font = subprocess.check_output(['fc-match', '-f', '%{file}', 'sans'], text=True)
im = Image.new('RGB', (1080, 450), '#090A0D')
d = ImageDraw.Draw(im)
title, label, small = [ImageFont.truetype(font, size) for size in (30, 16, 13)]
d.text((32,24), 'Sumi Red / Bibata + Apple', font=title, fill='#E6E0D9')
d.text((33,68), 'Bibata Modern pointer · native SVG sizes · no soft shadows', font=label, fill='#AAA39B')
for i, color in enumerate(['#E6E0D9', '#090A0D', '#D95757', '#9B454B']):
    x = 750 + i * 76
    d.rounded_rectangle((x,26,x+54,52), radius=6, fill=color, outline='#3A3D45')
    d.text((x-3,61), color, font=small, fill='#AAA39B')
items = [('Pointer','left_ptr.png'), ('Link','hand2.png'), ('Text','xterm.png'),
         ('Resize','bottom_right_corner.png'), ('Move','all-scroll.png'),
         ('Copy','copy.png'), ('Busy pointer','left_ptr_watch-01.png'), ('Waiting','wait-01.png')]
for i, (name, filename) in enumerate(items):
    x, y = 32 + i % 4 * 258, 110 + i // 4 * 162
    d.rounded_rectangle((x,y,x+242,y+146), radius=14, fill='#1A1C21', outline='#30333A')
    icon = Image.open(bitmaps/filename).convert('RGBA')
    assert icon.size == (96, 96)
    im.paste(icon, (x+73,y+8), icon)
    d.text((x+16,y+115), name, font=label, fill='#E6E0D9')
im.save(root.parent/'preview.png')
