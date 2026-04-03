import { realpathSync } from 'fs';

export default async ({ $ }) => {
  const pluginPath = new URL(import.meta.url).pathname;
  const realPluginPath = realpathSync(pluginPath);
  const pluginDir = new URL(".", `file://${realPluginPath}`).pathname;
  const ledScript = `${pluginDir}vibe.py`;
  const venvPython = `${pluginDir}.venv/bin/python`;

  let currentMode: 'on' | 'off' | 'idle' | 'plan' | 'build' = 'idle';
  let lastUpdate = 0;
  const MIN_INTERVAL_MS = 100;

  const sendLedCommand = async (mode: 'on' | 'off' | 'idle' | 'plan' | 'build') => {
    if (mode === currentMode) {
      return;
    }

    // Block direct transitions between plan and build
    if ((currentMode === 'plan' && mode === 'build') ||
        (currentMode === 'build' && mode === 'plan')) {
      return;
    }

    const now = Date.now();
    if (now - lastUpdate < MIN_INTERVAL_MS) {
      await new Promise(resolve => setTimeout(resolve, MIN_INTERVAL_MS));
    }

    currentMode = mode;
    lastUpdate = Date.now();
    await $`${venvPython} ${ledScript} ${mode}`;
  };

  return {
    "session.created": async () => {
      await sendLedCommand("on");
    },

    "session.deleted": async () => {
      await sendLedCommand("off");
    },

    event: async ({ event }) => {
      if (event.type === "message.updated") {
        const info = event.properties?.info;
        if (!info) return;

        // UserMessage has an "agent" field telling us which agent is active
        if (info.role === "user" && "agent" in info) {
          const agent = (info as any).agent;
          if (agent === "plan") {
            await sendLedCommand("plan");
          } else if (agent === "build") {
            await sendLedCommand("build");
          }
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
