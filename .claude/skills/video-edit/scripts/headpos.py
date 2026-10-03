#!/usr/bin/env python3
"""Head top / head x-span / body box per segment, read from the cutout alpha (assets/subject.webm).

Usage:  ~/.claude/skills/video-edit/.venv/bin/python headpos.py <project_dir>
Use it to place behind-head words (baseline ~30% of the x-height below the head top, see references/layout.md),
orbit rings, and cards that must not cover the face. Coordinates are in the 1080x1920 frame.
"""
import json
import os
import subprocess
import sys

from PIL import Image

proj = sys.argv[1]
segs = json.load(open(f'{proj}/segments.json'))
os.makedirs(f'{proj}/work/alpha', exist_ok=True)
for s in segs:
    t0, d = s['frame'] / 30, s['frames'] / 30
    rows = []
    for k, f in enumerate((.2, .5, .8)):
        png = f"{proj}/work/alpha/{s['id']}_{k}.png"
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-c:v', 'libvpx-vp9', '-ss', f'{t0 + d * f:.2f}',
                        '-i', f'{proj}/assets/subject.webm', '-frames:v', '1', '-vf', 'alphaextract,scale=270:480', png], check=True)
        im = Image.open(png).convert('L')
        px, (w, h) = im.load(), im.size
        ys = [y for y in range(h) if any(px[x, y] > 128 for x in range(0, w, 2))]
        if not ys:
            rows.append('no subject'); continue
        top = ys[0]
        xs = [x for x in range(w) if px[x, min(h - 1, top + 25)] > 128]
        bb = im.point(lambda v: 255 if v > 128 else 0).getbbox()
        rows.append(f"head top {top * 4:4d}  head x {xs[0] * 4}-{xs[-1] * 4}  body {[v * 4 for v in bb]}")
    print(f"{s['id']:8s} {t0:6.2f}s  " + ' | '.join(rows))
