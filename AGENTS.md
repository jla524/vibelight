# Agent Guidelines for Vibelight

This document helps agentic coding agents understand how to work with this repository.

## Project Overview

Vibelight controls a Govee Floor Lamp 2 (H607C) via LAN multicast. It provides mode-based breathing effects (plan/build/idle) with smooth transitions.

- **Language**: Python 3.12+
- **Package Manager**: uv
- **Structure**: Simple package with CLI entry point

## Build, Lint, and Test Commands

```bash
# Run the application
python vibe.py [on|plan|build|agent|idle|off]

# Cursor hook mode (reads JSON from stdin)
python vibe.py cursor-hook

# With uv
uv run python vibe.py plan

# Linting and formatting
ruff check .            # Check for linting errors
ruff format .           # Format all files
ruff check --fix .      # Auto-fix issues

# Dependency management
uv sync                 # Install dependencies from pyproject.toml
uv add <package>        # Add new dependency
uv pip list             # List installed packages
```

**Note**: No test suite is configured. To add tests, use `uv add --dev pytest` and create tests in a `tests/` directory.

## Code Style Guidelines

### Imports
- Use absolute imports for external packages
- Use relative imports within the `govee` package (e.g., `from . import udp`)
- Group imports: stdlib first, then third-party, then local
- No `from module import *` except in `__init__.py` for `__all__`

### Formatting
- Use ruff for formatting (consistent with Black style)
- 4 spaces for indentation
- No trailing whitespace
- Max line length: 88 characters (default ruff/black)

### Naming Conventions
- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_CASE` (e.g., `MCAST_GRP`, `DEVICE_CONTROL_PORT`)
- **Private methods**: `_leading_underscore`
- **Modules**: `snake_case.py`

### Type Hints
- Use type hints for function parameters and return values where non-obvious
- Simple types don't need hints (e.g., `status: str` is good)
- Complex data structures benefit from hints

### Documentation
- Use triple-quoted docstrings for all public functions and classes
- Format: brief description, then details if needed
- Keep first line under 72 characters

### Error Handling
- Use early returns with None for network/IO failures
- Handle socket timeouts explicitly (they raise exceptions)
- Clean up resources in `finally` blocks (sockets, threads)
- Print user-facing messages for important actions

### Threading
- Background effects use daemon threads
- Always provide a `stop()` method to gracefully terminate threads
- Use `threading.Event` for thread communication
- Join threads with timeout to avoid blocking indefinitely

### Architecture Patterns
- Keep UDP communication isolated in `udp.py`
- Device discovery in `discover.py`
- Main control logic in `GoveeLanDevice` class
- CLI entry point in `vibe.py`

### Constants
All Govee network constants are defined at module level:
- `MCAST_GRP`: Multicast group IP
- `MCAST_SEND_PORT` / `MCAST_RECV_PORT`: Discovery ports
- `DEVICE_CONTROL_PORT`: Command port (4003)

### Adding New Features
1. Implement device control methods in `GoveeLanDevice`
2. Update `__init__.py` exports if adding public API
3. Add CLI commands in `vibe.py`
4. Run `ruff check .` before committing
5. Test with actual hardware: `python vibe.py <mode>`

## Important Notes

- **Hardware dependency**: Code requires actual Govee device on network for testing
- **Network requirements**: Uses UDP multicast (ports 4001-4003)
- **Thread safety**: Effect threads are daemonized; call `stop()` before switching modes
- **Pure RGB mode**: For H607C, always use `temp=None` or `temp=0` to disable white channel

## Project Structure

```
/Users/jacky/repos/vibelight/
├── vibe.py                    # CLI entry point + cursor-hook subcommand
├── cursor_hooks.json          # Cursor hooks config
├── pyproject.toml             # Package config (uv-managed)
├── uv.lock                    # Locked dependencies
├── govee/                     # Vendored LAN control library
│   ├── __init__.py            # Exports GoveeLanDevice
│   ├── govee_lan_device.py    # Main device class
│   ├── discover.py            # Network discovery
│   └── udp.py                 # UDP communication
└── README.md
```

## Development Workflow

1. Make changes to code
2. Run `ruff check .` to verify style
3. Run `ruff format .` if needed
4. Test with `python vibe.py <mode>`
5. Verify effects work with actual hardware

## Cursor Hook Integration

`vibe.py cursor-hook` reads a JSON payload from stdin (as sent by Cursor's hook system) and maps events to lamp modes:

- **Agent events** (`beforeShellExecution`, `afterShellExecution`, `beforeMCPExecution`, `afterMCPExecution`, `beforeReadFile`, `afterFileEdit`, `beforeSubmitPrompt`, `afterAgentResponse`, `afterAgentThought`) → `agent` (purple)
- **Idle events** (`sessionStart`, `sessionEnd`, `stop`) → `idle` (gray)

Copy `cursor_hooks.json` to `.cursor/hooks.json` in any project to enable. Set `VIBELIGHT_DEBUG=1` for verbose stderr output.

## No Cursor/Copilot Rules

This repository does not contain `.cursorrules`, `.cursor/rules/`, or `.github/copilot-instructions.md` files.
