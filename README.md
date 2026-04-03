# Vibelight

A light that fits the vibe. Inspired by [claude-lamp](https://github.com/bobek-balinek/claude-lamp).

## Features
- Govee Floor Lamp 2 (H607C) control via LAN
- Mode-based breathing effects (plan/build/idle)
- Smooth transitions between modes
- Background effect management with `stop()` capability

## Quickstart

```bash
# Run with: `python vibe.py [plan|build|idle]`
python vibe.py idle

# Install as opencode plugin (auto-syncs lamp to agent state)
ln -s "$(pwd)/update_mode.ts" ~/.config/opencode/plugins/

# Turn on/off light when opencode starts/exits (add to ~/.zshrc)
export VIBELIGHT_DIR="/Users/dudu/repos/vibelight"
opencode() {
  "$VIBELIGHT_DIR/.venv/bin/python" "$VIBELIGHT_DIR/vibe.py" on
  command opencode "$@"
  "$VIBELIGHT_DIR/.venv/bin/python" "$VIBELIGHT_DIR/vibe.py" off
}
```
