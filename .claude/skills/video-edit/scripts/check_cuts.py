#!/usr/bin/env python3
"""Frame-exact QA of a render: the last frame before and first frame after every cut, in one strip, plus a phone copy.

Usage:  python3 check_cuts.py <project_dir> <render.mp4> [--phone]
Writes work/cut_check.jpg (pairs left->right: before|after for each cut). LOOK at it: every 'after' frame must show the
new shot with that section's look and no leftovers (room plates, cutout of the previous shot, stale captions).
Snapshots from `hyperframes snapshot` seek approximately at cuts; only frames pulled from the final render are proof.
--phone also writes <render>-phone.mp4 (720p, crf 26; SendUserFile uploads over ~5MB often fail, drop to crf 28).
"""
import json
import os
import subprocess
import sys

FF = 'ffmpeg'
proj, render = sys.argv[1], sys.argv[2]
segs = json.load(open(f'{proj}/segments.json'))
os.makedirs(f'{proj}/work/cf', exist_ok=True)
pngs = []
for s in segs[1:]:
    for n in (s['frame'] - 1, s['frame']):
        p = f'{proj}/work/cf/f{n}.png'
        subprocess.run([FF, '-loglevel', 'error', '-y', '-i', render, '-vf', f'select=eq(n\\,{n}),scale=150:-2', '-frames:v', '1', p], check=True)
        pngs.append(p)
ins = sum((['-i', p] for p in pngs), [])
subprocess.run([FF, '-loglevel', 'error', '-y', *ins, '-filter_complex', f'hstack={len(pngs)}', f'{proj}/work/cut_check.jpg'], check=True)
print('cuts at frames', [s['frame'] for s in segs[1:]], '->', f'{proj}/work/cut_check.jpg')
if '--phone' in sys.argv:
    out = render[:-4] + '-phone.mp4'
    subprocess.run([FF, '-loglevel', 'error', '-y', '-i', render, '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'slow',
                    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out], check=True)
    print('phone copy', out, f'{os.path.getsize(out) / 1e6:.1f} MB')
