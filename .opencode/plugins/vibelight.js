export const VibelightPlugin = async ({ project, $, directory }) => {
  // Turn on the light when a session starts
  return {
    "session.created": async () => {
      try {
        await $`python ${directory}/vibe.py on`.quiet()
      } catch (err) {
        // Silently ignore if light is unavailable
      }
    },

    // Turn off the light when the session ends
    "session.deleted": async () => {
      try {
        await $`python ${directory}/vibe.py off`.quiet()
      } catch (err) {
        // Silently ignore
      }
    },
  }
}
