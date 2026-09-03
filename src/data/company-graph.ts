export type GraphView = "company" | "goals" | "departments" | "work" | "intelligence" | "system";
export type GraphKind = "company" | "group" | "goal" | "department" | "agent" | "workflow" | "step" | "run" | "evidence" | "decision" | "memory" | "system" | "approval";

export type GraphNode = {
  id: string;
  type: GraphKind;
  label: string;
  state: string;
  metadata: Record<string, string>;
  source_ref: string;
  updated_at: string | null;
  views: GraphView[];
  summary?: string;
  diagnostic?: string;
};

export type GraphEdge = { id: string; type: string; from: string; to: string; metadata?: Record<string, string> };

const node = (id: string, type: GraphKind, label: string, state: string, views: GraphView[], metadata: Record<string, string> = {}, summary?: string, diagnostic?: string): GraphNode => ({
  id, type, label, state, views, metadata, summary, diagnostic,
  source_ref: type === "group" ? "visual projection" : ".spielos/state/company.sqlite",
  updated_at: metadata.Updated ?? null,
});

export const COMPANY_GRAPH = {
  snapshot: { generated_at: "2026-08-31T16:38:16.540941+00:00", runtime_version: "6.2.6", totals: { goals: 274, active_goals: 38, achieved_goals: 181, runs: 316, approvals: 275, evidence: 14717, decisions: 969, hypotheses: 101, memory: 0 } },
  nodes: [
    node("company:spielos", "company", "SpielOS", "running", ["company"], { Runtime: "6.2.6", Loop: "GOAL → OBSERVE → DECIDE → ACT → EVALUATE", Authority: ".spielos/state/company.sqlite" }, "One durable company loop. Every goal, run, approval, and evidence record is runtime-owned."),
    node("view:goals", "group", "Goals", "38 active", ["company"], {}, "274 total · 181 achieved · 49 abandoned"),
    node("view:departments", "group", "Departments", "7 installed", ["company"], {}, "Business capabilities plugged into the shared interpreter"),
    node("view:work", "group", "Work", "1 current run", ["company"], {}, "316 durable runs across execution, evaluation, and system improvement"),
    node("view:intelligence", "group", "Intelligence", "14,717 evidence", ["company"], {}, "969 decisions · 101 hypotheses"),
    node("view:memory", "group", "Memory", "0 claims", ["company"], {}, "No durable memory has been promoted", "14,717 evidence records exist, but durable memory is empty."),
    node("view:system", "group", "Systems", "attention", ["company"], {}, "Runner · approvals · watchdog · connections"),

    node("goal-11148124e5", "goal", "Book 1 qualified call per week", "active", ["goals"], { Owner: "director", Metric: "booked_calls ≥ 1", Stage: "DECIDE", Run: "run-ed91116159", Updated: "2026-08-30T09:46:20Z" }, "North Star: one qualified conversation per week proves the outbound machine creates revenue pipeline."),
    node("goal-d89ab679b0", "goal", "Recruitment send next 200 via Brevo", "blocked", ["goals", "work"], { Owner: "outbound", Workflow: "email-outreach", Stage: "DECIDE", Run: "run-e0789a7434", Updated: "2026-08-31T16:38:16Z" }),
    node("goal-cb9a336b6f", "goal", "Recruitment landing page mobile fix", "blocked", ["goals"], { Owner: "director", Stage: "DECIDE", Run: "run-6dcd3a6e9f", Updated: "2026-08-30T12:28:31Z" }),
    node("goal-c909b8b270", "goal", "Geo expansion research", "blocked", ["goals"], { Owner: "outbound", Workflow: "lead-research", Stage: "ACT" }),
    node("goal-9428806afb", "goal", "Receipt → Ledger re-record", "paused", ["goals"], { Owner: "videography", Workflow: "record_demo", Stage: "ACT", Run: "run-839390d107" }),

    node("agent:director", "agent", "Director", "orchestrating", ["departments"], { Role: "company director" }, "Owns goal intake, routing, supervision, evidence judgment, approvals, and outcome reporting."),
    node("department:analytics", "department", "Analytics", "installed", ["departments"], { Workflows: "4", Agents: "analytics-operator, cro-optimizer", Version: "3.3.0" }),
    node("department:client_delivery", "department", "Client delivery", "installed", ["departments"], { Workflows: "2", Agents: "delivery-manager, workflow-builder" }),
    node("department:content", "department", "Content", "installed", ["departments"], { Workflows: "5", Agents: "content-strategist, content-writer, publisher" }),
    node("department:design", "department", "Design", "installed", ["departments"], { Workflows: "4", Agents: "designer, video-producer" }),
    node("department:outbound", "department", "Outbound", "active", ["departments", "work"], { Workflows: "lead-research, email-outreach, social-lead-research, social-dm", Agents: "lead-researcher, social-researcher, outreach-writer" }),
    node("department:seo", "department", "SEO", "installed", ["departments"], { Workflows: "5", Agents: "seo-operator, seo-researcher" }),
    node("department:videography", "department", "Videography", "installed", ["departments"], { Workflows: "record_demo", Agents: "videography-operator, videography-specialist" }),

    node("workflow:email-outreach", "workflow", "Email outreach", "blocked", ["work"], { Department: "outbound", Steps: "select → compose → validate → approve → send → measure" }, "The documented bespoke stage exception, still inside the same company loop."),
    node("step:decide", "step", "DECIDE", "current", ["work"], { Workflow: "email-outreach" }, "A partial batch would change the planned run scope."),
    node("run-e0789a7434", "run", "run-e0789a7434", "blocked", ["work"], { Type: "execution", Owner: "outbound", Goal: "goal-d89ab679b0", Updated: "2026-08-31T16:38:16Z" }),
    node("dec-d7841a9bfbb1", "decision", "Request capability", "recorded", ["work"], { Type: "request_capability", Run: "run-e0789a7434" }, "A partial batch would change the planned run scope."),
    node("approval:current", "approval", "Human attention", "waiting", ["work"], { Goal: "goal-d89ab679b0", Run: "run-e0789a7434" }, "The next external action remains parked until explicitly approved."),

    node("ev-81b4c8e400c6", "evidence", "Director observation", "business", ["intelligence"], { Source: "director", Run: "run-6dcd3a6e9f", Goal: "goal-cb9a336b6f", Updated: "2026-08-30T12:28:31Z" }),
    node("ev-bde3ce356d35", "evidence", "Publication receipt", "business", ["intelligence"], { Source: "build + SEO verification", Run: "run-9a48941fd4", Updated: "2026-08-30T11:02:13Z" }),
    node("hypothesis:summary", "group", "101 hypotheses", "stored", ["intelligence"], {}, "Run-scoped predictions and resolution state"),
    node("dec-d49f07d7a463", "decision", "Package evidence meets the goal", "recorded", ["intelligence"], { Type: "evaluate", Run: "run-9a48941fd4", Updated: "2026-08-30T11:02:24Z" }),
    node("memory:empty", "memory", "Durable memory", "empty", ["intelligence"], { Count: "0", Gate: "valid evidence + future applicability" }, "No reusable claim has passed the evidence and applicability gate.", "Evidence is accumulating, but no claim has hardened into memory."),

    node("system:runtime", "system", "Company runtime", "running", ["system"], { Version: "6.2.6", Store: ".spielos/state/company.sqlite" }, "Single persisted company loop"),
    node("system:runner", "system", "Runner", "watching", ["system"], {}, "Bounded ticks, durable heartbeat, retry, and resume semantics"),
    node("system:watchdog", "system", "Watchdog", "monitoring", ["system"], {}, "Process, loop, dispatch, and send-activity liveness"),
    node("approval:summary", "approval", "275 approvals", "attention", ["system"], {}, "Live external actions always park for explicit approval"),
    node("system:work-orders", "system", "Work orders", "durable", ["system"], {}, "Atomic assignment boundary for employees and host workers"),
    node("system:connections", "system", "11 connections", "host resolved", ["system"], { Connections: "ActivePieces · Attio · Buffer · Cal · Email · Drive · Sheets · PostHog · Search Console · Web · Website" }),
  ] as GraphNode[],
  edges: [
    ...["goals", "departments", "work", "intelligence", "memory", "system"].map((id) => ({ id: `projects:${id}`, type: "projects", from: "company:spielos", to: `view:${id}` })),
    ...["goal-d89ab679b0", "goal-cb9a336b6f", "goal-c909b8b270", "goal-9428806afb"].map((id) => ({ id: `relates:${id}`, type: "relates_to", from: "goal-11148124e5", to: id })),
    ...["analytics", "client_delivery", "content", "design", "outbound", "seo", "videography"].map((id) => ({ id: `routes:${id}`, type: "routes_to", from: "agent:director", to: `department:${id}` })),
    { id: "owns:outbound", type: "owned_by", from: "goal-d89ab679b0", to: "department:outbound" },
    { id: "served:email", type: "served_by", from: "goal-d89ab679b0", to: "workflow:email-outreach" },
    { id: "stage:decide", type: "at_stage", from: "workflow:email-outreach", to: "step:decide" },
    { id: "run:current", type: "executed_as", from: "step:decide", to: "run-e0789a7434" },
    { id: "produced:decision", type: "produced", from: "run-e0789a7434", to: "dec-d7841a9bfbb1" },
    { id: "blocked:approval", type: "blocked_by", from: "run-e0789a7434", to: "approval:current" },
    { id: "tests:hyp", type: "tests", from: "ev-81b4c8e400c6", to: "hypothesis:summary" },
    { id: "supports:hyp", type: "supports", from: "ev-bde3ce356d35", to: "hypothesis:summary" },
    { id: "informs:decision", type: "informs", from: "hypothesis:summary", to: "dec-d49f07d7a463" },
    { id: "eligible:memory", type: "eligible_learning", from: "dec-d49f07d7a463", to: "memory:empty" },
    { id: "runtime:runner", type: "advanced_by", from: "system:runtime", to: "system:runner" },
    { id: "runtime:watch", type: "observed_by", from: "system:runtime", to: "system:watchdog" },
    { id: "runner:approvals", type: "parks", from: "system:runner", to: "approval:summary" },
    { id: "runner:orders", type: "dispatches", from: "system:runner", to: "system:work-orders" },
    { id: "orders:connections", type: "uses", from: "system:work-orders", to: "system:connections" },
  ] as GraphEdge[],
};

export const GRAPH_LAYOUTS: Record<GraphView, Record<string, [number, number]>> = {
  company: { "company:spielos": [0, 0], "view:goals": [0, -250], "view:departments": [270, -95], "view:work": [225, 185], "view:intelligence": [-225, 185], "view:memory": [-270, -95], "view:system": [0, 280] },
  goals: { "goal-11148124e5": [0, -230], "goal-d89ab679b0": [-260, -20], "goal-cb9a336b6f": [250, -20], "goal-c909b8b270": [-180, 210], "goal-9428806afb": [190, 210] },
  departments: { "agent:director": [0, 0], "department:analytics": [0, -250], "department:client_delivery": [235, -155], "department:content": [295, 100], "department:design": [130, 235], "department:outbound": [-130, 235], "department:seo": [-295, 100], "department:videography": [-235, -155] },
  work: { "goal-d89ab679b0": [-430, 0], "department:outbound": [-430, 160], "workflow:email-outreach": [-220, 0], "step:decide": [0, 0], "run-e0789a7434": [220, 0], "dec-d7841a9bfbb1": [420, -125], "approval:current": [420, 125] },
  intelligence: { "ev-81b4c8e400c6": [-380, -140], "ev-bde3ce356d35": [-380, 130], "hypothesis:summary": [-100, 0], "dec-d49f07d7a463": [175, 0], "memory:empty": [410, 0] },
  system: { "system:runtime": [0, -220], "system:runner": [-275, 0], "system:watchdog": [275, 0], "approval:summary": [-220, 215], "system:work-orders": [0, 255], "system:connections": [225, 215] },
};
