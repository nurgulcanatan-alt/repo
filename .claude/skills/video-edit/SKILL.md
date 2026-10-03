---
name: video-edit
description: "Turns raw 9:16 talking-head clips into a finished, premium Instagram reel end to end: picks the cleanest take of every line across your clips, cuts dead air, punches in from 4K, cuts you out of the background for words behind your head, applies one of three designed looks (bold kinetic words, cool girl, cool dude), builds animated UI inserts with parallel sub-agents, adds subtle sound design, and checks every cut frame by frame inside the Reels safe zone. Trigger with /video-edit or phrases like 'edit these clips', 'I dropped clips in my downloads', 'cut this into a reel', 'make this reel look fire'."
---

# /video-edit

Raw clips in, finished reel out. The user never opens an editor: they review a phone copy and give notes; every
round is a ~2 minute re-render.

Read before building: `references/looks.md` (the three looks, exact values), `references/layout.md` (safe zone,
placement, behind-head formula), `references/gotchas.md` (every trap already hit once). Read
`references/overlays.md` when the script calls for an animated insert.

## Step 0: First-time setup (runs once)

Look for `~/.claude/skills/video-edit/config.json`.

**If it exists:** load it (name, instagram handle, default look, folders) and go to Step 1.

**If it does not exist:**
1. Say: "Welcome to /video-edit! Let's get you set up. This takes about 2 minutes and only happens once."
2. Ask, in one message:
   - Your name (used on your Instagram profile insert)
   - Your Instagram handle (for your profile insert and to pull your reels for the orbit effect)
   - Default look: **bold** (kinetic words behind your head), **cool girl** (warm, yellow serif italic, your reels
     orbiting you) or **cool dude** (dark editorial, tracked caps + serif). Offer bold if they are unsure.
   - Where your raw clips usually land (default `~/Downloads`) and where projects should live (default `~/reel-edits`)
3. Run `zsh ~/.claude/skills/video-edit/scripts/setup.sh` and read the STATUS lines:
   - ffmpeg / node / python venv MISSING: give the exact fix the script printed and stop until it prints READY.
   - The script downloads the 6 sound effects itself. If it still reports them MISSING (offline), that is optional:
     the reel just has no SFX until they are added.
4. Optional, Apify (pulls reels and profile stats automatically): try a simple Apify MCP call. If it is not
   connected, say it is optional and how to add it:
   1. Create a free account at https://apify.com and copy the API token from Settings > API & Integrations.
   2. In a terminal, paste this one line with the token in place of YOUR_TOKEN:
      `claude mcp add apify -e APIFY_TOKEN=YOUR_TOKEN -- npx -y @apify/actors-mcp-server`
      (heads up: Claude Code stores the token in plain text in `~/.claude.json`; keep that file private).
   3. Reopen Claude and run /video-edit again.
   Without Apify, the skill asks them to drop their reel files into the project instead.
5. Save `~/.claude/skills/video-edit/config.json` (no secrets, ever):
   ```json
   {"name": "...", "instagram": "handle-without-@", "defaultLook": "bold", "clipsDir": "~/Downloads",
    "projectsDir": "~/reel-edits", "setupComplete": true, "setupDate": "YYYY-MM-DD"}
   ```
6. Say: "Setup complete! Running /video-edit now..." and continue.

`PY` below means `~/.claude/skills/video-edit/.venv/bin/python`, `SK` means `~/.claude/skills/video-edit`.

## Hard rules
1. Everything inside the Reels safe zone: top 220, bottom 450 (nothing below y 1470), sides 35, right 100 from y 1155.
2. Never cover the face with text or cards. Behind-head words show at least ~70% of each letter.
3. Captions say what was actually said: fix Whisper's mishearings of names and keywords ("Claude" often comes out
   as "cloud"/"claws", "skill" as "scale"). No em dashes in on-screen text.
4. Sound effects subtle (template `SFX_GAIN = 0.75` of the base volumes), never louder than the voice.
5. Credit other creators on screen (@handle) whenever their reels appear. Real numbers on the user's own profile;
   anything else (commenters, chat history) is a generic placeholder, never a real person, never fabricated proof.
6. Prove cuts from the final render, not from snapshots.
7. Never delete the user's files. Originals are read, never modified.

## Workflow

### 1. Intake
- Clips: the files the user names, else the newest video files in `clipsDir`. Create `<projectsDir>/<short-slug>/`.
- Reference links (IG reels, Pinterest pins) for a style: download them and look at frames before designing anything
  (see overlays.md for how to fetch them).

### 2. Ingest
```bash
PY SK/scripts/ingest.py <project> <clips or folder> [--newest 5]
```
Look at `work/sheets.jpg` (setups and angles) and read `transcript.txt` (per-clip lines, words with times, speech map).

### 3. Pick takes -> `<project>/edl.json`
- Rebuild the script from the takes: people repeat a line until it lands. Use the LAST complete clean take unless
  the user says otherwise ("the better section starts at 0:47" means one continuous take from there).
- In/out points from the speech map: start ~0.05-0.07s before the first word, end at the silence start after the
  last word. Kill dead air between sections; confirm short pauses with silencedetect before trimming (Whisper can
  invent a leading word at a cut).
- Two segments in a row from the same angle: punch one in (zoom 1.3-1.9 from the 4K original, cx/cy on the chest).
- Unsure words (keyword, CTA trigger): re-transcribe that snippet with medium.en and a prompt containing the names.
- Format: `[{"id": "hook", "clip": "c1", "in": 12.66, "out": 15.72, "zoom": 1.0, "cx": 0.5, "cy": 0.5, "line": "..."}]`
- Post the EDL to the user as a short table (line, clip, look per section) and keep going; do not wait.

### 4. Assemble, transcribe, cut out
```bash
python3 SK/scripts/assemble.py <project>            # aroll.mp4 clean 30fps CFR + segments.json with exact frames
PY SK/scripts/transcribe_cut.py <project> "<names and keywords in the script>"
zsh SK/scripts/cutout.sh <project>                  # run in background; asserts cutout frames == aroll frames
PY SK/scripts/headpos.py <project>                  # after the cutout: head/body position per segment
```

### 5. Inserts in parallel (as soon as the EDL is locked)
For each animated insert the script calls for (an app on screen, the profile follow on the CTA, a file scroll),
spawn a sub-agent in the background with the brief template in `references/overlays.md`: fixed size, fixed
duration, beats locked to the word times, transparent webm out. Keep building the main edit while they work.

### 6. Build
Copy `SK/assets/template/` into the project (build.py, hyperframes.json, package.json, assets/fonts, assets/sfx),
then adapt build.py. It is the finished build of a real reel: keep the machinery, rewrite the content (its
docstring lists which is which).
- Which look where: `defaultLook` for the whole reel; a line that names a look switches its section.
- Orbit and profile grid use the user's own reels (overlays.md: Apify post scraper with their handle, or files they
  drop into `assets/reels/`).
- Iterate: `npx --yes hyperframes@0.8.34 lint` (0 errors), then
  `SAFE=1 python3 build.py && npx --yes hyperframes@0.8.34 snapshot --at <10-20 moments> --no-end --describe false`,
  read the contact sheets, fix layout, readability and safe zone. (Node 22+: with nvm, `source ~/.nvm/nvm.sh && nvm use 22` first.)

### 7. Render and QA
```bash
python3 build.py      # without SAFE
npx --yes hyperframes@0.8.34 render -o renders/<slug>-vN.mp4 --quality high      # ~1.5-2 min for a 25s reel
python3 SK/scripts/check_cuts.py <project> renders/<slug>-vN.mp4 --phone
```
Look at `work/cut_check.jpg`: every after-cut frame shows the new shot cleanly. Check audio peaks (`volumedetect`,
max around -2 to -5 dB) and the silence at section joins.

### 8. Deliver
Send or point to the phone copy (720p) and the full-quality render. Report in plain terms what changed and anything
that needs the user's call. Keep every version in `renders/`; back up `assets/` + `segments.json` to `work/vN/` before
re-assembling.

## Defaults that came out of real feedback (do not re-litigate)
- Change the grade and captions to create a look; do not replace the background with an AI-generated room.
- No film grain. Dark is fine, but keep the subject lit and skin from going red.
- Lead-in captions centred in front of the speaker read better than lines pinned to the left edge.
- Words behind the head are the signature move, but only when readable.

---
Built by [@tenfoldmarc](https://instagram.com/tenfoldmarc). Follow for daily AI automation builds, real systems, not theory.
