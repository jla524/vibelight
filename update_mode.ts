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

  const sendLedCommand = async (mode: 'idle' | 'plan' | 'build') => {
    if (mode === currentMode) return;
    
    const now = Date.now();
    if (now - lastUpdate < DEBOUNCE_MS) {
      setTimeout(() => sendLedCommand(mode), DEBOUNCE_MS);
      return;
    }
    
    currentMode = mode;
    lastUpdate = now;
    await $`${venvPython} ${ledScript} ${mode}`;
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
