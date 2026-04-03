import { realpathSync } from 'fs';

export default async ({ $, client }) => {
  const pluginPath = new URL(import.meta.url).pathname;
  const realPluginPath = realpathSync(pluginPath);
  const pluginDir = new URL(".", `file://${realPluginPath}`).pathname;
  const ledScript = `${pluginDir}vibe.py`;
  const venvPython = `${pluginDir}.venv/bin/python`;

  let currentMode: 'idle' | 'plan' | 'build' | null = null;
  let lastUpdate = 0;
  const MIN_INTERVAL_MS = 500;

  const sendLedCommand = async (mode: 'idle' | 'plan' | 'build') => {
    if (mode === currentMode) {
      return;
    }

    const now = Date.now();
    const elapsed = now - lastUpdate;
    if (elapsed < MIN_INTERVAL_MS) {
      await new Promise(resolve => setTimeout(resolve, MIN_INTERVAL_MS - elapsed));
    }

    try {
      await $`${venvPython} ${ledScript} ${mode}`.quiet();
      currentMode = mode;
      lastUpdate = Date.now();
    } catch (err) {
      console.error(`Failed to send LED command "${mode}":`, err);
    }
  };

  return {
    event: async ({ event }) => {
      if (event.type === "message.updated") {
        const info = event.properties?.info;
        if (!info) return;

        if (info.role === "user" && typeof info === "object" && "agent" in info) {
          const agent = info.agent;
          if (agent === "plan" || agent === "build") {
            await sendLedCommand(agent);
          }
        }
      }

      if (event.type === "session.idle") {
        await sendLedCommand("idle");
      }
    }
  };
};
