import { realpathSync } from 'fs';

export default async ({ $ }) => {
  const pluginPath = new URL(import.meta.url).pathname;
  const realPluginPath = realpathSync(pluginPath);
  const pluginDir = new URL(".", `file://${realPluginPath}`).pathname;
  const ledScript = `${pluginDir}vibe.py`;
  const venvPython = `${pluginDir}.venv/bin/python`;

  let currentMode: 'idle' | 'plan' | 'build' = 'idle';
  let lastUpdate = 0;
  const DEBOUNCE_MS = 100;
  const STABILITY_MS = 300; // Require 300ms of stability before changing
  let pendingMode: 'idle' | 'plan' | 'build' | null = null;
  let stabilityTimer: ReturnType<typeof setTimeout> | null = null;

  const sendLedCommand = async (mode: 'idle' | 'plan' | 'build') => {
    if (mode === currentMode) {
      // Cancel any pending change if we're back to current mode
      if (stabilityTimer) {
        clearTimeout(stabilityTimer);
        stabilityTimer = null;
      }
      pendingMode = null;
      return;
    }
    
    // Debounce rapid event spam
    const now = Date.now();
    if (now - lastUpdate < DEBOUNCE_MS) {
      setTimeout(() => sendLedCommand(mode), DEBOUNCE_MS);
      return;
    }
    
    // If this is a new mode request, start stability timer
    if (pendingMode !== mode) {
      pendingMode = mode;
      
      // Clear any existing timer
      if (stabilityTimer) {
        clearTimeout(stabilityTimer);
      }
      
      // Set timer to actually change mode after stability period
      stabilityTimer = setTimeout(() => {
        currentMode = mode;
        lastUpdate = Date.now();
        pendingMode = null;
        stabilityTimer = null;
        $`${venvPython} ${ledScript} ${mode}`;
      }, STABILITY_MS);
    }
  };

  return {
    event: async ({ event }) => {
      if (event.type === "message.part.updated") {
        const part = event.properties?.part;
        if (!part) return;

        if (part.type === "reasoning") {
          await sendLedCommand("plan");
        } else if (part.type === "tool" || part.type === "step-start") {
          await sendLedCommand("build");
        }
      }

      if (event.type === "session.status") {
        const status = event.properties?.status;
        if (status?.type === "idle") {
          await sendLedCommand("idle");
        }
      }

      if (event.type === "session.idle") {
        await sendLedCommand("idle");
      }
    }
  };
};
