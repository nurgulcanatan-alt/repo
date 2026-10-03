#!/bin/bash
# The video-edit skill hardcodes ~/.claude/skills/video-edit, so link the project copy there.
mkdir -p "$HOME/.claude/skills"
target="$HOME/.claude/skills/video-edit"
[ -e "$target" ] && [ ! -L "$target" ] && exit 0  # keep a real install if one exists
ln -sfn "$CLAUDE_PROJECT_DIR/.claude/skills/video-edit" "$target"
