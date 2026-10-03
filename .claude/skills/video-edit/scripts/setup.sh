#!/bin/zsh
# /video-edit first-run checks. Safe to re-run: it only reports and fills in what is missing.
#   1. ffmpeg + ffprobe on PATH
#   2. Node 22+ (HyperFrames renders with it; nvm is used if present)
#   3. Python venv inside the skill with faster-whisper + Pillow (transcription, head tracking)
#   4. Sound effects library in assets/template/assets/sfx (not bundled: Pixabay license forbids redistributing the files)
# Prints a STATUS line per item; exit code 0 only when everything is ready.
SKILL=${0:A:h:h}
ok=1

if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then
  echo "STATUS ffmpeg OK ($(ffmpeg -version | head -1 | cut -d' ' -f3))"
else
  echo "STATUS ffmpeg MISSING -> Mac: brew install ffmpeg | Linux: sudo apt install ffmpeg | Windows: winget install ffmpeg"; ok=0
fi

[[ -s ~/.nvm/nvm.sh ]] && source ~/.nvm/nvm.sh >/dev/null && nvm use 22 >/dev/null 2>&1
nodev=$(node -v 2>/dev/null | sed 's/v//' | cut -d. -f1)
if [[ -n "$nodev" && "$nodev" -ge 22 ]]; then
  echo "STATUS node OK ($(node -v))"
else
  echo "STATUS node MISSING or < 22 -> install Node 22 LTS from https://nodejs.org (or: nvm install 22)"; ok=0
fi

if [[ -x "$SKILL/.venv/bin/python" ]] && "$SKILL/.venv/bin/python" -c "import faster_whisper, PIL" 2>/dev/null; then
  echo "STATUS python venv OK"
elif command -v python3 >/dev/null; then
  echo "STATUS python venv: creating $SKILL/.venv (faster-whisper + Pillow, ~1 min)"
  python3 -m venv "$SKILL/.venv" && "$SKILL/.venv/bin/pip" install -q --upgrade pip && "$SKILL/.venv/bin/pip" install -q faster-whisper pillow \
    && echo "STATUS python venv OK" || { echo "STATUS python venv FAILED (see pip output above)"; ok=0; }
else
  echo "STATUS python3 MISSING -> install Python 3.10+ from https://python.org"; ok=0
fi

SFX="$SKILL/assets/template/assets/sfx"
mkdir -p "$SFX"
need=(whoosh-short pop sparkle click click-soft impact-bass-1)
for lib in ~/.claude/skills/media-use/audio/assets/sfx ~/.agents/skills/media-use/audio/assets/sfx; do
  [[ -d "$lib" ]] && for n in $need; do [[ -f "$SFX/$n.mp3" ]] || cp "$lib/$n.mp3" "$SFX/" 2>/dev/null; done
done
# not found locally: fetch them from the HyperFrames repo, which publishes this Pixabay-licensed pack
RAW=https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/audio/assets/sfx
for n in $need; do [[ -s "$SFX/$n.mp3" ]] || curl -fsSL "$RAW/$n.mp3" -o "$SFX/$n.mp3" 2>/dev/null || true; done
missing=(); for n in $need; do [[ -s "$SFX/$n.mp3" ]] || missing+=$n; done
if (( ${#missing} == 0 )); then
  echo "STATUS sound effects OK"
else
  echo "STATUS sound effects MISSING: ${missing[*]} -> optional. Download similar free SFX from https://pixabay.com/sound-effects/"
  echo "        and save them as $SFX/<name>.mp3, then re-run this script."
fi

(( ok )) && echo "READY" || echo "NOT READY"
(( ok ))
