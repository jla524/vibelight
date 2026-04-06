#!/usr/bin/env bun
/**
 * Cursor hook for Vibelight - Updates Govee lamp based on agent session state
 *
 * Usage: Add to ~/.cursor/hooks.json:
 * {
 *   "version": 1,
 *   "hooks": {
 *     "sessionStart": [{ "command": "bun run /Users/jacky/repos/vibelight/cursor_update_mode.ts" }],
 *     "sessionEnd": [{ "command": "bun run /Users/jacky/repos/vibelight/cursor_update_mode.ts" }]
 *   }
 * }
 */

import { execSync } from "child_process";

// State management
let currentMode: "idle" | "agent" | null = null;
let lastUpdate = 0;
const MIN_INTERVAL_MS = 500;

const sendLedCommand = (mode: "idle" | "agent") => {
    if (mode === currentMode) {
        return;
    }

    const now = Date.now();
    const elapsed = now - lastUpdate;
    if (elapsed < MIN_INTERVAL_MS) {
        Bun.sleepSync(MIN_INTERVAL_MS - elapsed);
    }

    try {
        execSync(`vibe ${mode}`, { stdio: "pipe" });
        currentMode = mode;
        lastUpdate = Date.now();
    } catch (err) {
        console.error(`Failed to send LED command "${mode}":`, err);
    }
};

// Read JSON input from stdin
const input = await Bun.stdin.text();
const payload = JSON.parse(input);

const hookEvent = payload.hook_event_name;
const composerMode = payload.composer_mode;

// Handle different hook events
if (hookEvent === "sessionStart") {
    // Agent mode sessions trigger the "agent" lighting mode (purple)
    if (composerMode === "agent") {
        sendLedCommand("agent");
    }
} else if (hookEvent === "sessionEnd") {
    // Session ending returns to idle
    sendLedCommand("idle");
}

// Output empty JSON (required by Cursor hooks protocol)
console.log(JSON.stringify({}));
