#!/usr/bin/env python3
"""Build a GRUB theme and an illustrative preview; does not edit boot configuration."""
from pathlib import Path
import shutil
import subprocess
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = Path('/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Regular.ttf')
BOLD = Path('/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Bold.ttf')
W, H = 1920, 1080
WHITE, MUTED, DIM = '#e7e9ec', '#979da5', '#626870'

# The outer desktop is pure black. The terminal panel has only a slight lift.
im = Image.new('RGB', (W, H), '#000000')
d = ImageDraw.Draw(im)
x, y, right, bottom = 346, 248, 1574, 832
d.rounded_rectangle((x,y,right,bottom), radius=12, fill='#090a0c', outline='#303339', width=1)
d.line((x+1, y+53, right-1, y+53), fill='#24272b')
for i, color in enumerate(('#73777e', '#454950', '#30343a')):
    d.ellipse((x+27+i*22,y+23,x+35+i*22,y+31), fill=color)
im.save(ROOT/'background.png')
# Supersampled monochrome icons. GRUB selects icons by menuentry --class.
icons = ROOT/'icons'
icons.mkdir(exist_ok=True)
def make_icon(kind):
    icon=Image.new('RGBA',(128,128),(0,0,0,0));q=ImageDraw.Draw(icon)
    color='#d5d9df'
    if kind=='arch':
        q.polygon([(64,7),(12,119),(47,101),(64,95),(81,101),(116,119)],fill=color)
        q.ellipse((49,69,79,123),fill=(0,0,0,0))
        q.polygon([(34,58),(50,68),(39,48)],fill=(0,0,0,0))
        q.polygon([(79,47),(97,76),(76,65)],fill=(0,0,0,0))
    elif kind=='windows':
        for a,b,c,e in [(12,16,58,61),(66,16,112,61),(12,69,58,114),(66,69,112,114)]:
            q.rectangle((a,b,c,e),fill=color)
    elif kind=='firmware':
        points=[]
        for i in range(64):
            angle=i*math.tau/64
            radius=54 if i%8 in (0,1,2,3) else 43
            points.append((64+radius*math.cos(angle),64+radius*math.sin(angle)))
        q.polygon(points,fill=color)
        q.ellipse((43,43,85,85),fill=(0,0,0,0))
    else:
        q.rounded_rectangle((12,16,116,112),radius=12,outline=color,width=7)
        q.line((31,45,47,60,31,75),fill=color,width=7)
        q.line((61,80,94,80),fill=color,width=7)
    return icon.resize((32,32),Image.Resampling.LANCZOS)
for kind,names in [('arch',['arch','archlinux']),('windows',['windows']),
                   ('firmware',['firmware','uefi','efi','fwsetup','bios']),
                   ('generic',['os','linux','gnu-linux','gnu','unknown','recovery'])]:
    for name in names:make_icon(kind).save(icons/f'{name}.png')
# A nine-slice selection panel, compatible with GRUB's styled boxes.
for name, size in [('c',(8,8)),('w',(4,8)),('e',(4,8)),('n',(8,1)),('s',(8,1)),('nw',(4,1)),('ne',(4,1)),('sw',(4,1)),('se',(4,1))]:
    tile=Image.new('RGB',size,'#181b20')
    if name in ('w','nw','sw'):
        ImageDraw.Draw(tile).rectangle((0,0,1,size[1]-1),fill='#dce2e7')
    tile.save(ROOT/f'select_{name}.png')

for size in (16,20,24):
    subprocess.run(['grub-mkfont','-n','Void Mono','-s',str(size),'-r','0x20-0x7e,0xa0-0x17f,0x400-0x4ff,0x2190-0x2193',
                    '-o',str(ROOT/f'void-{size}.pf2'),str(FONT)],check=True)
shutil.copyfile('/usr/share/licenses/ttf-jetbrains-mono-nerd/OFL.txt',ROOT/'FONT-LICENSE.txt')

theme='''# Void Terminal — standard GRUB gfxmenu theme. No custom modules.
# Reference mode: 1920x1080. Menu labels always come from grub.cfg.
title-text: ""
desktop-image: "background.png"
desktop-image-scale-method: "stretch"
desktop-color: "#000000"
terminal-font: "Void Mono Regular 20"
terminal-left: "18%"
terminal-top: "23%"
terminal-width: "64%"
terminal-height: "54%"
terminal-border: "0"

+ label {
  left = 18%
  top = 24%+7
  width = 64%
  align = "center"
  font = "Void Mono Regular 16"
  color = "#979da5"
  text = "boot@localhost: ~"
}
+ label {
  left = 22%
  top = 33%
  width = 56%
  font = "Void Mono Regular 20"
  color = "#979da5"
  text = "boot@localhost:~$ select --target"
}
+ label {
  left = 22%
  top = 37%
  width = 56%
  font = "Void Mono Regular 16"
  color = "#626870"
  text = "Choose an operating system."
}
+ boot_menu {
  left = 22%
  top = 43%
  width = 56%
  height = 23%
  item_font = "Void Mono Regular 24"
  selected_item_font = "Void Mono Regular 24"
  item_color = "#979da5"
  selected_item_color = "#e7e9ec"
  item_height = 48
  item_spacing = 10
  item_padding = 16
  icon_width = 32
  icon_height = 32
  item_icon_space = 18
  selected_item_pixmap_style = "select_*.png"
  scrollbar = false
}
+ label {
  left = 22%
  top = 68%
  width = 56%
  font = "Void Mono Regular 16"
  color = "#626870"
  text = "[UP/DOWN] select   [ENTER] boot   [E] edit   [C] console"
}
+ label {
  id = "__timeout__"
  left = 22%
  top = 71%
  width = 56%
  font = "Void Mono Regular 16"
  color = "#979da5"
  text = "Starting selected system in %d s"
}
+ progress_bar {
  id = "__timeout__"
  left = 22%
  top = 75%
  width = 56%
  height = 2
  show_text = false
  fg_color = "#c9cfd5"
  bg_color = "#23262b"
  border_color = "#23262b"
}
'''
(ROOT/'theme.txt').write_text(theme)
# This preview uses the same assets, coordinates, colors, and source font.
# It is a design mockup, not a screenshot of a running GRUB instance.
preview=im.copy();p=ImageDraw.Draw(preview)
def label(text,x,y,size,color):
    p.text((x,y),text,font=ImageFont.truetype(str(FONT),size),fill=color)
title='boot@localhost: ~';f=ImageFont.truetype(str(FONT),16)
label(title,(W-p.textlength(title,font=f))/2,274,16,MUTED)
label('boot@localhost:~$ select --target',422,356,20,MUTED)
label('Choose an operating system.',422,400,16,DIM)
for i,text in enumerate(['Arch Linux','Windows','UEFI Firmware Settings']):
    yy=464+i*58
    if i==0:
        p.rectangle((422,yy,1497,yy+47),fill='#181b20')
        p.rectangle((422,yy,423,yy+47),fill='#dce2e7')
    icon=Image.open(icons/(['arch','windows','firmware'][i]+'.png'))
    preview.paste(icon,(442,yy+8),icon)
    label(text,492,yy+9,24,WHITE if i==0 else MUTED)
label('[UP/DOWN] select   [ENTER] boot   [E] edit   [C] console',422,734,16,DIM)
label('Starting selected system in 5 s',422,767,16,MUTED)
p.rectangle((422,810,1497,811),fill='#23262b')
p.rectangle((422,810,1190,811),fill='#c9cfd5')
preview.save(ROOT/'preview.png')
print(ROOT/'preview.png')
