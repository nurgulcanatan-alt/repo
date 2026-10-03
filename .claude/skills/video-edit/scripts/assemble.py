#!/usr/bin/env python3
"""Cut the reel straight from the originals into <project>/assets/aroll.mp4 (1080x1920, clean 30fps CFR from t=0).

Usage:  python3 assemble.py <project_dir>
Needs <project>/sources.json (from ingest.py) and <project>/edl.json:
  [{"id": "hook", "clip": "c1", "in": 12.66, "out": 15.72, "zoom": 1.0, "cx": 0.5, "cy": 0.5, "line": "Everybody's..."}, ...]
  zoom > 1 = punch-in cropped from the original (sharp when the source is 4K), centred on (cx, cy) as frame fractions.
Writes segments.json with each segment's first frame in the cut ("frame") and frame count ("frames").

Why the CFR re-encode: ffmpeg concat leaves a 0.033s video start offset and timestamp gaps; `hyperframes remove-background`
then duplicates frames and the cutout drifts out of sync with the base video by the end. setpts=N/30 fixes it.
"""
import json
import os
import subprocess
import sys

FF, FP = 'ffmpeg', 'ffprobe'


def size(f):
    w, h = subprocess.run([FP, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', f],
                          capture_output=True, text=True).stdout.strip().split(',')[:2]
    return int(w), int(h)


def crop(z, cx, cy, sw, sh):
    if z <= 1:
        return ''
    w, h = round(sw / z / 2) * 2, round(sh / z / 2) * 2
    x = min(max(round(cx * sw - w / 2), 0), sw - w)
    y = min(max(round(cy * sh - h / 2), 0), sh - h)
    return f'crop={w}:{h}:{x}:{y},'


def frames(f):
    return int(subprocess.run([FP, '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames',
                               '-of', 'csv=p=0', f], capture_output=True, text=True).stdout)


def main():
    proj = sys.argv[1]
    src = json.load(open(f'{proj}/sources.json'))
    edl = json.load(open(f'{proj}/edl.json'))
    os.makedirs(f'{proj}/work', exist_ok=True)
    os.makedirs(f'{proj}/assets', exist_ok=True)
    parts, meta = [], []
    for k, s in enumerate(edl):
        f = src[s['clip']]
        sw, sh = size(f)
        d = s['out'] - s['in']
        out = f'{proj}/work/seg_{k}.mp4'
        # vertical fill: scale to cover 1080x1920 then centre-crop (handles 4K 9:16 and odd phone sizes)
        vf = (f"{crop(s.get('zoom', 1), s.get('cx', .5), s.get('cy', .5), sw, sh)}"
              'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30')
        subprocess.run([FF, '-loglevel', 'error', '-y', '-ss', f"{s['in']:.3f}", '-t', f'{d:.3f}', '-i', f,
                        '-map', '0:v:0', '-map', '0:a:0', '-vf', vf,
                        '-af', f'afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03',   # no clicks at the joins
                        '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                        '-c:a', 'pcm_s16le', '-ar', '48000', out], check=True)
        parts.append(out)
        meta.append({**s, 'src_in': s['in'], 'src_out': s['out']})
    open(f'{proj}/work/concat.txt', 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p in parts))
    subprocess.run([FF, '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{proj}/work/concat.txt',
                    '-vf', 'setpts=N/30/TB', '-r', '30', '-fps_mode', 'cfr', '-af', 'asetpts=PTS-STARTPTS',
                    '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '30', '-keyint_min', '30', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', f'{proj}/assets/aroll.mp4'], check=True)
    fr = 0
    for k, m in enumerate(meta):
        n = frames(parts[k])
        m['frame'], m['frames'] = fr, n
        fr += n
    json.dump(meta, open(f'{proj}/segments.json', 'w'), indent=1)
    for m in meta:
        print(f"frame {m['frame']:4d} ({m['frame'] / 30:6.3f}s) +{m['frames']:3d}f  {m['id']:8s} {m['clip']} {m['in']}-{m['out']}  {m.get('line', '')}")
    total = frames(f'{proj}/assets/aroll.mp4')
    print(f'total frames {fr} (aroll.mp4 has {total})' + ('' if total == fr else '  << MISMATCH, investigate'))


if __name__ == '__main__':
    main()
