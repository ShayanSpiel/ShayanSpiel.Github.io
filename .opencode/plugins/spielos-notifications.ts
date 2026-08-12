import type { Plugin } from "@opencode-ai/plugin"

const REPORTABLE = new Set([
  "approval_required",
  "action_required",
  "blocked",
  "failed",
  "run_completed",
  "goal_achieved",
  "goal_abandoned",
  "goal_expired",
])

export const SpielOSNotifications: Plugin = async ({ client, directory, $ }) => {
  const shell = $.cwd(directory).env({
    ...process.env,
    PYTHONDONTWRITEBYTECODE: "1",
    PYTHONPATH: ".agents",
  })
  let checking = false
  const prompted = new Map<string, number>()

  const check = async () => {
    if (checking) return
    checking = true
    try {
      const status = JSON.parse(
        await shell`python3 -B -m company runner status`.text(),
      ) as { enabled?: boolean }
      if (status.enabled === false) return
      await shell`python3 -B -m company runner tick`.quiet().nothrow()
      const raw = await shell`python3 -B -m company notifications list --status pending --limit 100`.text()
      const pending = (JSON.parse(raw) as Array<{
        id: string
        kind: string
        payload?: { approval_interaction?: Record<string, unknown> }
      }>).filter(
        (item) => REPORTABLE.has(item.kind),
      )
      const pendingIDs = new Set(pending.map((item) => item.id))
      for (const id of prompted.keys()) {
        if (!pendingIDs.has(id)) prompted.delete(id)
      }
      const now = Date.now()
      const fresh = pending.filter((item) => now - (prompted.get(item.id) ?? 0) > 300_000)
      if (!fresh.length) return
      fresh.forEach((item) => prompted.set(item.id, now))
      const ids = fresh.map((item) => item.id)
      const approvals = fresh.filter(
        (item) => item.kind === "approval_required" && item.payload?.approval_interaction,
      )
      if (activeSessionID) {
        for (const item of approvals) {
          // The native question is an agent tool, not a plugin API. Wake the
          // Director with one typed interaction; it must ask before acting.
          await client.session.promptAsync({
            path: { id: activeSessionID },
            query: { directory },
            body: {
              agent: "director",
              parts: [{
                type: "text",
                text: [
                  "A SpielOS action is parked for approval.",
                  "Immediately invoke the native question tool with exactly the supplied interaction.",
                  "Show Approve and Reject separately. Do not combine this with another approval.",
                  "Run the fallback command only after an explicit Approve answer.",
                  "On Reject, leave the action parked and report that nothing executed.",
                  JSON.stringify(item.payload?.approval_interaction),
                ].join("\n"),
              }],
            },
          })
        }
      }
      await client.tui.showToast({
        query: { directory },
        body: {
          title: "SpielOS Director",
          message: `${ids.length} company run update${ids.length === 1 ? "" : "s"} ready`,
          variant: fresh.some((item) => ["failed", "blocked", "action_required"].includes(item.kind))
            ? "warning"
            : "success",
          duration: 8000,
        },
      })
    } catch {
      // The durable outbox remains pending; the next idle check retries safely.
    } finally {
      checking = false
    }
  }

  const timer = setInterval(check, 5000)
  let activeSessionID: string | undefined

  return {
    dispose: async () => clearInterval(timer),
    event: async ({ event }) => {
      if (event.type === "session.idle") {
        activeSessionID = event.properties.sessionID
        await check()
      }
    },
    "command.execute.before": async (input) => {
      if (input.command === "stop") {
        await shell`python3 -B -m company runner stop`.quiet()
      } else if (input.command === "start") {
        await shell`python3 -B -m company runner enable`.quiet()
      }
    },
  }
}

export default SpielOSNotifications
