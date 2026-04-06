# Vibelight

A light that fits the vibe. Inspired by [claude-lamp](https://github.com/bobek-balinek/claude-lamp).

<img src="demo.gif" height="480" alt="Vibelight Demo">

## Features
- Govee Floor Lamp 2 (H607C) control via LAN
- Mode-based breathing effects (plan/build/idle)
- Smooth transitions between modes
- Background effect management with `stop()` capability

## Quickstart

### 1. Install to PATH

Add the `vibe` command to your PATH so it's available anywhere:

```bash
# Ensure ~/.local/bin exists and is in your PATH
mkdir -p ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"  # Add to ~/.zshrc if not already there

# Create symlink
ln -s /Users/jacky/repos/vibelight/vibe.py ~/.local/bin/vibe
```

### 2. Install opencode plugin

```bash
# Symlink the plugin to opencode's plugin directory
ln -s /Users/jacky/repos/vibelight/update_mode.ts ~/.config/opencode/plugins/
```

### 3. Optional: Turn on/off with opencode

Add to your `~/.zshrc`:

```bash
alias opencode="vibe on && \opencode && vibe off"
```

### Manual usage

```bash
vibe idle    # Calm breathing (white)
vibe plan    # Energetic breathing (orange)
vibe build   # Balanced breathing (blue)
vibe on      # Turn on steady light
vibe off     # Turn off
```
