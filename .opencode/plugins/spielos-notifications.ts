import type { Plugin } from "@opencode-ai/plugin"
import { readFile } from "node:fs/promises"
import { join } from "node:path"

const REPORTABLE = new Set([
  "approval_required",
  "action_required",
  "blocked",
  "failed",
  "run_completed",
  "goal_achieved",
  "goal_abandoned",
  "goal_expired",
  "runner_down",
  "stuck_goal",
])

// A daemon whose heartbeat stamp is older than this is treated as down even
// when its pid still looks alive (hung or wedged watch loop). The runner
// stamps .spielos/state/runner.heartbeat at the start of every watch cycle.
const HEARTBEAT_STALE_MS = 75_000
const HEARTBEAT_RELATIVE = ".spielos/state/runner.heartbeat"

type NotificationItem = {
  id: string
  kind: string
  payload?: {
    approval_interaction?: Record<string, unknown>
    watchdog?: { signal?: string }
  }
}

export const SpielOSNotifications: Plugin = async ({ client, directory, $ }) => {
  const shell = $.cwd(directory).env({
    ...process.env,
    PYTHONDONTWRITEBYTECODE: "1",
    PYTHONPATH: ".agents",
  })
  let checking = false
  const prompted = new Map<string, number>()

  const heartbeatAgeMs = async (): Promise<number | null> => {
    try {
      const raw = await readFile(join(directory, HEARTBEAT_RELATIVE), "utf8")
      const parsed = JSON.parse(raw) as { last_tick?: string }
      const lastTick = parsed.last_tick ? Date.parse(parsed.last_tick) : Number.NaN
      if (Number.isNaN(lastTick)) return null
      return Date.now() - lastTick
    } catch {
      return null
    }
  }

  const check = async () => {
    if (checking) return
    checking = true
    try {
      const status = JSON.parse(
        await shell`python3 -B -m company runner status --json`.text(),
      ) as { enabled?: boolean; running?: boolean }
      if (status.enabled === false) return
      // The daemon watch loop owns the tick while it is running; only tick
      // ourselves when no daemon is around, so the two never race the lease.
      if (status.running !== true) {
        await shell`python3 -B -m company runner tick`.quiet().nothrow()
      }
      // Runner-down detection (inverted silent skip): alert when the polled
      // status says not running OR the heartbeat stamp went stale. A missing
      // heartbeat file is not stale on its own (a pre-heartbeat daemon must
      // not false-positive); a dead daemon always fails the status check.
      const heartbeatAge = await heartbeatAgeMs()
      const runnerDown =
        status.running !== true ||
        (heartbeatAge !== null && heartbeatAge > HEARTBEAT_STALE_MS)
      const pendingRaw = await shell`python3 -B -m company notifications list --status pending --limit 100 --json`.text()
      const deliveredRaw = await shell`python3 -B -m company notifications list --status delivered --limit 100 --json`.text()
      const byID = new Map<string, NotificationItem>()
      for (const item of [
        ...(JSON.parse(deliveredRaw) as NotificationItem[]),
        ...(JSON.parse(pendingRaw) as NotificationItem[]),
      ]) {
        // Pending wins on duplicate ids: it is the fresher state.
        byID.set(item.id, item)
      }
      const recent = [...byID.values()].filter(
        (item) => REPORTABLE.has(item.kind),
      )
      const recentIDs = new Set(recent.map((item) => item.id))
      for (const id of prompted.keys()) {
        // The synthesized runner-down key is not a notification id and must
        // survive the prune or its throttle resets on every check.
        if (!recentIDs.has(id) && id !== "runner-down") prompted.delete(id)
      }
      const now = Date.now()
      const fresh = recent.filter((item) => now - (prompted.get(item.id) ?? 0) > 300_000)
      if (!fresh.length && !runnerDown) return
      fresh.forEach((item) => prompted.set(item.id, now))
      const ids = fresh.map((item) => item.id)
      const watchdog = fresh.find((item) => item.payload?.watchdog?.signal)
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
      if (runnerDown) {
        // Inverted silent skip: a chat-visible alert exactly when the runner
        // is down, throttled by the same re-prompt window as notifications so
        // a long outage does not spam.
        if (now - (prompted.get("runner-down") ?? 0) > 300_000) {
          prompted.set("runner-down", now)
          const ageSeconds = heartbeatAge === null ? null : Math.round(heartbeatAge / 1000)
          await client.tui.showToast({
            query: { directory },
            body: {
              title: "SpielOS runner down",
              message: `The runner daemon is not ticking${ageSeconds === null ? "" : ` (heartbeat age ${ageSeconds}s)`}. Restart with \`company runner start\`.`,
              variant: "warning",
              duration: 8000,
            },
          })
          if (activeSessionID) {
            await client.session.promptAsync({
              path: { id: activeSessionID },
              query: { directory },
              body: {
                agent: "director",
                parts: [{
                  type: "text",
                  text: [
                    "The SpielOS runner daemon appears down (no fresh heartbeat).",
                    "Restart it with `company runner start`, then verify with `company runner status`.",
                  ].join("\n"),
                }],
              },
            })
          }
        }
      } else if (fresh.length) {
        const watchdogSignal = watchdog?.payload?.watchdog?.signal
        await client.tui.showToast({
          query: { directory },
          body: {
            title:
              watchdogSignal === "stuck_goal"
                ? "SpielOS stuck goal"
                : watchdogSignal === "runner_down"
                  ? "SpielOS runner down"
                  : "SpielOS Director",
            message: `${ids.length} company run update${ids.length === 1 ? "" : "s"} ready`,
            variant: fresh.some((item) => ["failed", "blocked", "action_required"].includes(item.kind))
              ? "warning"
              : "success",
            duration: 8000,
          },
        })
      }
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
