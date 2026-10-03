#!/bin/zsh
# Cut the speaker out of the assembled cut -> <project>/assets/subject.webm (VP9 + alpha), then verify it is
# frame-for-frame the same length as aroll.mp4 (a mismatch means the cutout will drift; re-run assemble.py).
# Usage: cutout.sh <project_dir>      (~35s per 5s of footage on Apple Silicon / CoreML; slower on CPU)
# The first run downloads the segmentation model.
set -e
cd "$1"
if [[ -s ~/.nvm/nvm.sh ]]; then source ~/.nvm/nvm.sh >/dev/null; nvm use 22 >/dev/null 2>&1 || true; fi
npx --yes hyperframes@0.8.34 remove-background assets/aroll.mp4 -o assets/subject.webm --quality best 2>&1 | tail -1
a=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 assets/aroll.mp4)
s=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 assets/subject.webm)
echo "aroll frames $a / cutout frames $s"
[[ "$a" == "$s" ]] || { echo "FRAME MISMATCH: cutout will drift. Re-run assemble.py (clean CFR) then this script."; exit 1; }
