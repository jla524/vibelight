import { realpathSync } from 'fs';

export default async ({ $, client }) => {
  const pluginPath = new URL(import.meta.url).pathname;
  const realPluginPath = realpathSync(pluginPath);
  const pluginDir = new URL(".", `file://${realPluginPath}`).pathname;
  const ledScript = `${pluginDir}vibe.py`;
  const venvPython = `${pluginDir}.venv/bin/python`;

  let currentMode: 'idle' | 'plan' | 'build' | null = null;
  let isIdle = false;
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

    currentMode = mode;
    lastUpdate = Date.now();

    try {
      await $`${venvPython} ${ledScript} ${mode}`.quiet();
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
          if (agent === "plan") {
            isIdle = false;
            await sendLedCommand("plan");
          } else if (agent === "build") {
            isIdle = false;
            await sendLedCommand("build");
          }
        }
      }

      if (event.type === "session.idle") {
        isIdle = true;
        await sendLedCommand("idle");
      }
    }
  };
};
