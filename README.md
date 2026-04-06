# Vibelight

A light that fits the vibe. Inspired by [claude-lamp](https://github.com/bobek-balinek/claude-lamp).

<img src="demo.gif" height="480" alt="Vibelight Demo">

## Features
- Govee Floor Lamp 2 (H607C) control via LAN multicast
- Five lighting modes: plan (orange), build (blue), agent (purple), idle (white), on/off
- Pure RGB mode for accurate color reproduction (no white channel mixing)
- Automatic device discovery via UDP multicast
- Opencode plugin for automatic mode switching based on agent activity
- Cursor hooks support for agent session integration
- CLI with graceful signal handling for cleanup

## Quickstart

Navigate to where you cloned the repo, then run these commands:

```bash
cd /path/to/vibelight
```

> **Note on absolute paths**: The symlinks below use `$(pwd)` to resolve the full path. We use absolute symlinks for reliability—they won't break if you move between directories, and they clearly indicate where the source files live. While relative symlinks work too, absolute paths are less fragile for configuration files.

### 1. Install to PATH

Add the `vibe` command to your PATH so it's available anywhere:

```bash
# Ensure ~/.local/bin exists and is in your PATH
mkdir -p ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"  # Add to ~/.zshrc if not already there

# Create symlink using absolute path of current directory
ln -s "$(pwd)/vibe.py" ~/.local/bin/vibe
```

### 2. Install opencode plugin

```bash
# Symlink the plugin to opencode's plugin directory
ln -s "$(pwd)/update_mode.ts" ~/.config/opencode/plugins/
```

### 2b. Install Cursor hooks (optional)

```bash
# Symlink the hooks config to Cursor's config directory
ln -s "$(pwd)/cursor_hooks.json.example" ~/.cursor/hooks.json
```

The Cursor hook activates "agent" mode (purple breathing) when an Agent session starts, and returns to "idle" (white) when the session ends.

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
vibe agent   # Creative breathing (purple) - for Cursor agent mode
vibe on      # Turn on steady light
vibe off     # Turn off
```
