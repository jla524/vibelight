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
```
