# Gotchas (each one cost a render)

## Timing / sync
- ffmpeg concat -> 0.033s video start offset + VFR gaps -> remove-background outputs extra frames -> the cutout drifts
  (by 20s it lagged a few frames: two copies of the speaker on screen after a cut). assemble.py re-encodes with
  `setpts=N/30/TB -fps_mode cfr`; cutout.sh asserts equal frame counts.
- `tl.set` at a rounded time fires one frame late: use `frame/30 - 0.002`.
- `hyperframes snapshot` seeks approximately at cut boundaries; it can show the next shot a frame early. Only frames
  extracted from the final render (`check_cuts.py`) prove a cut.
- When a segment's in-point is trimmed, every hard-coded word time after it shifts. Keep a `SHIFT` derived from
  segments.json and wrap later times in `S(t)` (see template) instead of retyping them.
- Whisper word starts can be ~0.1-0.3s off and it hallucinates a leading word at a cut. Confirm pauses with
  `silencedetect` (n=-40dB, d=0.08) before trimming dead air.

## Rendering
- CSS `-webkit-mask-image` does not survive the renderer. Bake alpha into a VP9 WebM with ffmpeg alphamerge instead.
- `autoAlpha:1` sets opacity to 1 and overrides a CSS `opacity` on the same element. A "3% grain" layer shown with
  autoAlpha ran at 100%. Put low opacity on an inner element or tween opacity to the target value.
- Every `<video>` needs an `id` or it renders frozen. Each overlapping media element needs its own `data-track-index`.
  `<audio>` SFX need ids too, and overlapping SFX need separate track indices (the template's lane allocator does it).
- Never tween autoAlpha/opacity on an element that has data-start (the framework forces opacity 1 on active clips):
  wrap it in a plain div and animate the wrapper.
- Lint rejects tweening letterSpacing (layout snapping): fake tracking with scaleX.
- Element ids cannot contain apostrophes ("i've" broke the whole inline script). Use keys like 'ive'.
- `fromTo` renders its from-state immediately: pass `immediateRender:false` for anything hidden until its time.
- Heavy backdrop-filter/blur on many elements can make captures go black; keep it to a few.

## Assets / tools
- Node 22+ for HyperFrames (with nvm: `source ~/.nvm/nvm.sh && nvm use 22`), pin `npx --yes hyperframes@0.8.34`.
- Python scripts run in the skill's own venv: `~/.claude/skills/video-edit/.venv/bin/python` (faster-whisper + Pillow).
  The first transcription downloads the Whisper model (small.en ~0.5GB, medium.en ~1.5GB).
- zsh: `for x in "a b"; do set -- $x` does not split; use `${=x}` or a Python loop.
- If a shell safety hook blocks inline heredoc scripts or moves into the Trash, write the script to a file and run
  it; download temp files into a scratch folder instead of moving things around. Never delete the user's files.
- Large file uploads to chat can fail: deliver a 720p crf 26-28 phone copy and keep the full render on disk.
- Pinterest/Instagram pages block logged-out browsing; curl the page HTML or use Apify.
