import { realpathSync } from 'fs';

export default async ({ $, client }) => {
  const pluginPath = new URL(import.meta.url).pathname;
  const realPluginPath = realpathSync(pluginPath);
  const pluginDir = new URL(".", `file://${realPluginPath}`).pathname;
  const ledScript = `${pluginDir}vibe.py`;
  const venvPython = `${pluginDir}.venv/bin/python`;

  let currentMode: 'on' | 'off' | 'idle' | 'plan' | 'build' = 'idle';
  let lastUpdate = 0;
  const MIN_INTERVAL_MS = 500;
  let currentSessionId: string | null = null;

  const sendLedCommand = async (mode: 'on' | 'off' | 'idle' | 'plan' | 'build') => {
    if (mode === currentMode) {
      return;
    }

    const now = Date.now();
    if (now - lastUpdate < MIN_INTERVAL_MS) {
      await new Promise(resolve => setTimeout(resolve, MIN_INTERVAL_MS));
    }

    currentMode = mode;
    lastUpdate = Date.now();
    await $`${venvPython} ${ledScript} ${mode}`.quiet();
  };

  const detectAgentFromSession = async () => {
    if (!currentSessionId) return;
    try {
      const session = await client.session.get({ path: { id: currentSessionId } });
      const messages = await client.session.messages({ path: { id: currentSessionId } });
      const lastMessage = messages[messages.length - 1];
      if (lastMessage?.info?.role === "user" && "agent" in lastMessage.info) {
        const agent = (lastMessage.info as any).agent;
        if (agent === "plan" || agent === "build") {
          await sendLedCommand(agent);
        }
      }
    } catch {
      // Session may not exist yet
    }
  };

  return {
    "session.created": async ({ event }) => {
      currentSessionId = event?.properties?.session?.id || null;
      await sendLedCommand("on");
    },

    "session.deleted": async () => {
      currentSessionId = null;
      await sendLedCommand("off");
    },

    event: async ({ event }) => {
      if (event.type === "message.updated") {
        const info = event.properties?.info;
        if (!info) return;

        // Detect agent switches from user messages
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
