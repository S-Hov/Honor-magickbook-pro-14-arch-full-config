// Render upstream SVG shapes using the Sumi Red palette.
const fs = require('node:fs');
const path = require('node:path');
const { Resvg } = require('@resvg/resvg-js');
const out = process.argv[2];
fs.mkdirSync(out, { recursive: true });
const dark = [0x6b, 0x30, 0x34], light = [0xff, 0x90, 0x90];
function color(match) {
  const c = match.toUpperCase();
  if (c === '#E6E0D9' || c === '#090A0D') return c;
  if (c === '#00FF00' || c === '#FFFFFF') return '#E6E0D9';
  if (c === '#0000FF' || c === '#000000') return '#090A0D';
  if (c === '#00C500') return '#D95757';
  if (c === '#009200') return '#9B454B';
  const rgb = [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16));
  if (Math.max(...rgb) - Math.min(...rgb) < 12) return match;
  const t = Math.max(0, Math.min(1, ((rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722) / 255 - .12) / .72));
  return '#' + dark.map((v, i) => Math.round(v + (light[i] - v) * t).toString(16).padStart(2, '0')).join('');
}
function walk(dir) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) { walk(p); continue; }
    if (!p.endsWith('.svg')) continue;
    const svg = fs.readFileSync(p, 'utf8').replace(/\bwhite\b/gi, '#E6E0D9').replace(/\bblack\b/gi, '#090A0D').replace(/#[0-9a-f]{6}\b/gi, color);
    const png = new Resvg(svg).render().asPng();
    fs.writeFileSync(path.join(out, ent.name.replace(/\.svg$/, '.png')), png);
  }
}
walk(path.join(__dirname, 'svg'));
