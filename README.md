# Vibelight

A light that fits the vibe. Controls a Govee Floor Lamp 2 (H607C) via LAN multicast. Provides mode-based breathing effects with smooth transitions.

<img src="demo.gif" height="480" alt="Vibelight Demo">

## Features
- Pure LAN control (no cloud required)
- Modes: `plan` (energetic orange), `build` (balanced blue), `idle` (calm gray)
- `on`/`off` controls
- Background effect threads with graceful stop
- Opencode AI integration for automatic session lighting

## Installation

```bash
# Using uv (recommended)
uv sync

# Run directly
uv run python vibe.py idle
```

## Usage

```bash
python vibe.py [on|plan|build|idle|off]
```

- `plan`: Orange breathing for focused work
- `build`: Blue for development
- `idle`: Neutral gray
- `on`/`off`: Basic power control

The script auto-discovers the device on first run.

## Opencode Plugin

The `.opencode/plugins/vibelight.js` plugin turns the light on at session start and off at session end.

See `.opencode/` for configuration.

## Development

```bash
# Lint and format
ruff check .
ruff format .

# See AGENTS.md for full guidelines, architecture, and code style
```

Project uses the vendored `govee/` package for UDP multicast communication.

