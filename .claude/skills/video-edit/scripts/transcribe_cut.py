#!/usr/bin/env python3
"""Word timings for the assembled cut -> <project>/words.json (medium.en; these drive every caption).

Usage:  ~/.claude/skills/video-edit/.venv/bin/python transcribe_cut.py <project_dir> ["prompt with names: Claude, Claude Code, skill"]
Whisper mishears proper nouns ("Claude" -> "cloud"/"claws", "skill" -> "scale", "design" -> "this line"):
pass them in the prompt and still fix captions by hand from what the speaker actually said.
"""
import json
import subprocess
import sys

from faster_whisper import WhisperModel

proj = sys.argv[1]
prompt = sys.argv[2] if len(sys.argv) > 2 else 'Claude, Claude Code, skill.'
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f'{proj}/assets/aroll.mp4', '-vn', '-ac', '1',
                '-ar', '16000', f'{proj}/work/aroll.wav'], check=True)
m = WhisperModel('medium.en', compute_type='int8')
s, _ = m.transcribe(f'{proj}/work/aroll.wav', word_timestamps=True, vad_filter=False, initial_prompt=prompt)
ws = [{'text': w.word.strip(), 'start': round(w.start, 3), 'end': round(w.end, 3)} for x in s for w in x.words]
json.dump(ws, open(f'{proj}/words.json', 'w'), indent=1)
print(' '.join(f"{w['text']}@{w['start']:.2f}" for w in ws))
