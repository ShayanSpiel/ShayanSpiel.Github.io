import CodexComposer from './CodexComposer';
import ThesisAssembly from './ThesisAssembly';
import PracticalSurface from './PracticalSurface';
import {compactDetails} from './compact-story';
import { LocalizedContent } from './Localization';
import type { CSSProperties } from 'react';
import LangSmithSurface from './LangSmithSurface';
import { TeamAssembly, HarnessAssembly, MemoryAssembly } from './AssemblySurface';
import { surfaceIcons } from './surface-icons';
import { definitions, type Tile } from './scenes';
export const logoNames: Record<string, string> = { 'claude-code': 'Claude Code', codex: 'Codex', opencode: 'OpenCode', n8n: 'n8n', python: 'Python', salesforce: 'Salesforce', zendesk: 'Zendesk', 'openai-chatgpt': 'ChatGPT', elevenlabs: 'ElevenLabs', remotion: 'Remotion', activepieces: 'Activepieces', zapier: 'Zapier', notion: 'Notion', trello: 'Trello', langfuse: 'Langfuse', 'langsmith-langchain': 'LangSmith' };
const aliases: Record<string, string> = { building: 'buildings', layers: 'layer', bolt: 'bolt-circle', plug: 'link', 'check-shield': 'shield', 'bar-chart': 'bar-chart-alt-2' };
export function SurfaceIcon({ name }: {
    name: string;
}) { return <span className="deck-vector" aria-hidden="true" dangerouslySetInnerHTML={{ __html: surfaceIcons[aliases[name] || name] || surfaceIcons['network-chart'] }}/>; }
export function Providers({ logos }: {
    logos: string[];
}) { return <div className="deck-providers"><LocalizedContent value={logos.map(logo => <span key={logo}><img className={['opencode', 'openai-chatgpt'].includes(logo) ? 'deck-monochrome-logo' : undefined} src={['activepieces','elevenlabs'].includes(logo) ? `/assets/infrastructure/logos/${logo}.svg` : logo === 'remotion' ? '/assets/infrastructure/logos/remotion.png' : `/assets/infrastructure/logos/thesvg/${logo}.svg`} width="28" height="28" alt=""/><b><LocalizedContent value={logoNames[logo] || logo}/></b></span>)}/></div>; }
const management = ['goal', 'observe', 'decide', 'act', 'evaluate'];
const spec: Record<string, [
    string,
    string
][]> = {
    goal: [['Business outcome', 'Resolve customer requests faster'], ['Quality floor', 'Accurate answers. Policy respected.'], ['Accountable owner', 'Head of Customer Support']],
    observe: [['Follow the work', 'From the first ticket to the final reply'], ['Find the friction', 'Handoffs, waiting, rework and errors'], ['Listen to people', 'Customer feedback and team experience']],
    decide: [['Choose the opportunity', 'Resolve common questions first'], ['Design the change', 'Retrieve knowledge. Draft. Validate.'], ['Set the boundary', 'Escalate exceptions to a person']],
    act: [['Build the workflow', 'Connect knowledge, agents and tools'], ['Keep control', 'Review sensitive decisions'], ['Put it into use', 'Run alongside the current process']],
    evaluate: [['Compare with the goal', 'Time, cost and response quality'], ['Keep the evidence', 'Results, exceptions and feedback'], ['Choose the next move', 'Improve, expand or stop']],
};
function Spec({ rows }: {
    rows: [
        string,
        string
    ][];
}) { return <div className="deck-spec"><LocalizedContent value={rows.map(([label, value], i) => <div key={label}><span className="deck-spec-index"><LocalizedContent value={"0"}/><LocalizedContent value={i + 1}/></span><div><span><LocalizedContent value={label}/></span><strong><LocalizedContent value={value}/></strong></div></div>)}/></div>; }
function ValueVisual() { return <div className="deck-value-visual"><div className="deck-value-question"><span className="deck-eyebrow"><LocalizedContent value={"START WITH VALUE"}/></span><strong><LocalizedContent value={"How can AI create a better business outcome?"}/></strong></div><div className="deck-value-metrics"><div><b><LocalizedContent value={"Handling time"}/></b><strong><LocalizedContent value={"≤6 min"}/></strong><span><LocalizedContent value={"from 12 min baseline"}/></span></div><div><b><LocalizedContent value={"Economics"}/></b><strong><LocalizedContent value={"≤$6"}/></strong><span><LocalizedContent value={"from $8 per resolution"}/></span></div><div><b><LocalizedContent value={"Quality"}/></b><strong><LocalizedContent value={"≥95%"}/></strong><span><LocalizedContent value={"quality acceptance target"}/></span></div></div><footer><SurfaceIcon name="target-lock"/><LocalizedContent value={"Illustrative pilot targets · validate before scaling."}/></footer></div>; }
function WorkLayersVisual() { return <div className="deck-work-layers"><div className="deck-layer deck-layer--task"><span><LocalizedContent value={"01"}/></span><div><b><LocalizedContent value={"Tasks"}/></b><small><LocalizedContent value={"Individual actions people and tools perform."}/></small></div><strong><LocalizedContent value={"one action"}/></strong></div><div className="deck-layer deck-layer--workflow"><span><LocalizedContent value={"02"}/></span><div><b><LocalizedContent value={"Workflows"}/></b><small><LocalizedContent value={"Connected tasks with decisions, owners and outcomes."}/></small></div><strong><LocalizedContent value={"one result"}/></strong></div><div className="deck-layer deck-layer--system"><span><LocalizedContent value={"03"}/></span><div><b><LocalizedContent value={"Systems"}/></b><small><LocalizedContent value={"Repeatable ways of working with memory, controls and evidence."}/></small></div><strong><LocalizedContent value={"compounding capability"}/></strong></div><footer><SurfaceIcon name="layers"/><LocalizedContent value={"Transformation moves from a task to a system of work."}/></footer></div>; }
function GoalVisual() { return <div className="deck-goal-visual"><div className="deck-goal-metrics"><div><strong><LocalizedContent value={"≤6 min"}/></strong><span><LocalizedContent value={"handling time · from 12 min"}/></span></div><div><strong><LocalizedContent value={"≤$6"}/></strong><span><LocalizedContent value={"cost per resolution · from $8"}/></span></div><div><strong><LocalizedContent value={"1"}/></strong><span><LocalizedContent value={"workflow at a time"}/></span></div></div><div className="deck-goal-target"><SurfaceIcon name="target-lock"/><span><b><LocalizedContent value={"Illustrative pilot · ≥95% quality"}/></b><small><LocalizedContent value={"More useful work, measured against today\u2019s baseline."}/></small></span></div><footer><LocalizedContent value={"Owner \u00B7 quality bar \u00B7 evidence for the next decision"}/></footer></div>; }
function ManagementInput({ node }: {
    node: Tile;
}) { const logos = node.id === 'goal-inputs' ? ['notion', 'trello'] : ['notion', 'trello', 'langfuse']; return <div className="deck-management-input"><span className="deck-eyebrow"><LocalizedContent value={node.id === 'goal-inputs' ? 'MANAGEMENT RECORDS' : 'CONNECTED EVIDENCE'}/></span><div className="deck-tool-row"><LocalizedContent value={logos.map(logo => <span key={logo}><img src={`/assets/infrastructure/logos/thesvg/${logo}.svg`} alt=""/><b><LocalizedContent value={logo[0].toUpperCase() + logo.slice(1)}/></b></span>)}/></div><ul><LocalizedContent value={(node.rows || []).map(row => <li key={row}><span className="deck-row-bullet"/><LocalizedContent value={row}/></li>)}/></ul></div>; }
function SystemGrid() { const items = [['context', 'Context', 'Understands your business'], ['semantic', 'Memory', 'Retains what matters'], ['runtime', 'Harness', 'Orchestrates execution'], ['providers', 'Tools', 'Acts in your systems'], ['guardrails', 'Guardrails', 'Enforces your rules'], ['observability', 'Observability', 'Makes every run visible']]; return <><div className="deck-os-topline"><span><i /><LocalizedContent value={"AI OS / SHARED FOUNDATION"}/></span><small><LocalizedContent value={"RUNS \u00B7 EVALS \u00B7 TOOL REGISTRY"}/></small></div><div className="deck-system-grid"><LocalizedContent value={items.map(([id, label, note], i) => <div key={id} style={{ '--cell-tone': `var(--${['primary', 'success', 'accent', 'primary', 'warning', 'accent'][i]})` } as CSSProperties}><SurfaceIcon name={definitions[id].icon}/><strong><LocalizedContent value={label}/></strong><span><LocalizedContent value={note}/></span></div>)}/></div></>; }
function ContextCells() { return <div className="deck-context-cells"><LocalizedContent value={['Strategy', 'Policies', 'Processes', 'Knowledge', 'People', 'Systems', 'Data', 'APIs'].map((label, i) => <div key={label}><SurfaceIcon name={['target-lock', 'shield', 'cog', 'book-open', 'group', 'chip', 'data', 'link'][i]}/><span><LocalizedContent value={label}/></span></div>)}/></div>; }
function RuntimeVisual() {
    const point = (angle: number) => [165 + 105 * Math.cos(angle * Math.PI / 180), 148 + 105 * Math.sin(angle * Math.PI / 180)];
    const arcs = [[-64, -12], [54, 104], [174, 224]].map(([from, to]) => { const a = point(from), b = point(to); return `M ${a[0]} ${a[1]} A 105 105 0 0 1 ${b[0]} ${b[1]}`; });
    return <div className="deck-runtime-loop"><svg viewBox="0 0 330 300" aria-hidden="true"><defs><marker id="deck-runtime-arrow" viewBox="0 0 8 8" refX="6" refY="4" markerWidth="5" markerHeight="5" orient="auto"><path d="M1 1 6 4 1 7" fill="none" stroke="currentColor" strokeWidth="1.2"/></marker></defs><circle cx="165" cy="148" r="105"/><LocalizedContent value={arcs.map(d => <path key={d} d={d} markerEnd="url(#deck-runtime-arrow)"/>)}/></svg><div className="deck-loop-center"><small><LocalizedContent value={"UNTIL COMPLETE"}/></small><strong><LocalizedContent value={"One run."}/></strong></div><LocalizedContent value={[['Reason', 'brain'], ['Use tools', 'link'], ['Observe', 'show']].map(([label, icon], i) => <div className={`deck-orbit-step deck-orbit-step--${i}`} key={label}><SurfaceIcon name={icon}/><b><LocalizedContent value={label}/></b></div>)}/></div>;
}
function FrictionVisual() { return <div className="deck-friction"><div className="deck-ticket-preview"><span className="deck-eyebrow"><LocalizedContent value={"SUPPORT \u00B7 NEW REQUEST"}/></span><strong><LocalizedContent value={"\u201CCan you help with my order?\u201D"}/></strong><small><LocalizedContent value={"A simple question enters a complicated process."}/></small></div><div className="deck-handoffs"><LocalizedContent value={[['Read', 'user'], ['Search', 'search'], ['Ask', 'message-square'], ['Reply', 'check-circle']].map(([label, icon], i) => <div key={label}><SurfaceIcon name={icon}/><b><LocalizedContent value={label}/></b><LocalizedContent value={i < 3 && <span><LocalizedContent value={"\u2192"}/></span>}/></div>)}/></div><div className="deck-friction-caption"><SurfaceIcon name="history"/><span><LocalizedContent value={"Value waits between the steps."}/></span></div></div>; }
function WorkflowVisual({ process = false }: {
    process?: boolean;
}) { return <div className="deck-workflow-example"><div className="deck-example-label"><span><LocalizedContent value={process ? 'PROCESS CONTRACT' : 'FIRST WORKFLOW · SUPPORT'}/></span><b><LocalizedContent value={"Request \u2192 Resolution"}/></b></div><div className="deck-workflow-stages"><LocalizedContent value={(process ? [['Input', 'Customer request', 'message-square'], ['Decisions', 'Policy + judgment', 'brain'], ['Action', 'Resolve the issue', 'cog']] : [['Understand', 'Classify the request', 'search'], ['Prepare', 'Retrieve + draft', 'file'], ['Resolve', 'Validate + respond', 'check-circle']]).map(([label, note, icon], i) => <div key={label}><span className="deck-stage-icon"><SurfaceIcon name={icon}/></span><div><b><LocalizedContent value={label}/></b><small><LocalizedContent value={note}/></small></div><LocalizedContent value={i < 2 && <span className="deck-stage-arrow"><LocalizedContent value={"\u2193"}/></span>}/></div>)}/></div><div className="deck-outcome-line"><SurfaceIcon name="target-lock"/><LocalizedContent value={process ? 'A defined outcome, owner and quality bar.' : 'Measure resolution time, cost and quality.'}/></div></div>; }
function MemoryVisual({ id }: {
    id: string;
}) {
    const data: Record<string, {
        label: string;
        title: string;
        rows: [
            string,
            string
        ][];
        footer: string;
    }> = {
        procedural: { label: 'PROCEDURAL MEMORY · A REUSABLE METHOD', title: 'Resolve a delivery question', rows: [['01', 'Verify the order and customer'], ['02', 'Check delivery status and policy'], ['03', 'Resolve or escalate the exception']], footer: 'Skills · Playbooks · Procedures · Templates' },
        semantic: { label: 'SEMANTIC MEMORY · A DURABLE FACT', title: 'Company knowledge, ready to use', rows: [['Policy', 'Returns follow the approved policy'], ['Product', 'Specifications come from the catalog'], ['Source', 'Keep the reference and update date']], footer: 'Facts · Concepts · Company knowledge' },
        episodic: { label: 'EPISODIC MEMORY · A PAST EXPERIENCE', title: 'The previous run left a lesson', rows: [['Situation', 'A delivery exception needed review'], ['Decision', 'Escalated to the support owner'], ['Lesson', 'Check this exception earlier next time']], footer: 'Runs · Decisions · Outcomes' },
    };
    const d = data[id];
    return <div className="deck-memory-record"><span className="deck-eyebrow"><LocalizedContent value={d.label}/></span><strong className="deck-record-title"><LocalizedContent value={d.title}/></strong><div><LocalizedContent value={d.rows.map(([label, value]) => <div className="deck-record-row" key={label}><span><LocalizedContent value={label}/></span><b><LocalizedContent value={value}/></b></div>)}/></div><footer><SurfaceIcon name="book-open"/><LocalizedContent value={d.footer}/></footer></div>;
}
function CapabilityGrid({ id }: {
    id: string;
}) {
    const groups: Record<string, [
        string,
        string,
        string
    ][]> = {
        workers: [['Research', 'Gather evidence', 'search'], ['Build', 'Produce the work', 'code-alt'], ['Analyze', 'Find the signal', 'bar-chart'], ['Review', 'Verify the result', 'shield']],
        departments: [['Sales', 'Research → Qualified pipeline', 'group'], ['Support', 'Request → Resolution', 'support'], ['Marketing', 'Insight → Campaign', 'trending-up'], ['Finance', 'Invoice → Reconciliation', 'receipt']],
        research: [['Architecture', 'Define how the pieces work together', 'layers'], ['Models', 'Match reasoning to the work', 'brain'], ['Integrations', 'Connect existing systems and tools', 'link']],
        guardrails: [['Correct', 'Meets the task and quality requirements', 'check-square'], ['Safe', 'Respects policy, access and approval', 'shield'], ['Complete', 'Required work is finished and recorded', 'check-circle']],
        outcomes: [['More capacity', 'Teams spend less time on repetitive work', 'rocket'], ['Better economics', 'Lower cost for each completed outcome', 'trending-up'], ['Reliable quality', 'Standards are checked on every run', 'shield']],
    };
    return <div className={`deck-capability-grid deck-capability-grid--${id}`}><LocalizedContent value={groups[id].map(([title, note, icon], i) => <div key={title} style={{ '--capability-tone': `var(--${['primary', 'success', 'accent', 'warning'][i]})` } as CSSProperties}><SurfaceIcon name={icon}/><div><b><LocalizedContent value={title}/></b><small><LocalizedContent value={note}/></small></div><LocalizedContent value={id === 'guardrails' && <span className="deck-check"><LocalizedContent value={"\u2713"}/></span>}/></div>)}/></div>;
}
function BuildPipeline({ id }: {
    id: string;
}) {
    const rows: Record<string, [
        string,
        string
    ][]> = {
        builder: [['Retrieve', 'Find relevant facts, methods and history'], ['Select', 'Keep only what this task needs'], ['Compose', 'Build a focused working brief']],
        episode: [['Capture', 'Summarize the run and its outcome'], ['Review', 'Identify a fact or a better method'], ['Retain', 'Make the lesson available next time']],
        engineering: [['Build', 'Agents and workflows perform the work'], ['Connect', 'Tools reach the systems of record'], ['Verify', 'Tests and evaluations protect quality']],
        analysis: [['Map', 'Follow the actual work end to end'], ['Diagnose', 'Locate waiting, rework and bottlenecks'], ['Prioritize', 'Find a valuable, practical first change']],
        current: [['People', 'Who owns each handoff and decision?'], ['Information', 'Which facts and systems do they need?'], ['Constraints', 'What must remain safe and correct?']],
        redesign: [['Simplify', 'Remove unnecessary steps and handoffs'], ['Define', 'Make decisions and quality criteria explicit'], ['Preserve', 'Keep human judgment at the right points']],
        parallel: [['100 comparable cases', 'Proposed pilot · same inputs for both workflows'], ['12 → ≤6 minutes', 'Target handling time · measured against baseline'], ['≥95% quality', 'No critical policy failures · owner approves release']],
    };
    return <Spec rows={rows[id]}/>;
}
function DirectorVisual() { return <div className="deck-accountability"><span className="deck-eyebrow"><LocalizedContent value={"ONE ACCOUNTABLE OWNER"}/></span><div className="deck-owner-scope"><LocalizedContent value={[['Priorities', 'What matters most', 'target-lock'], ['Architecture', 'How it fits together', 'layers'], ['Outcomes', 'Whether it worked', 'trending-up']].map(([title, note, icon]) => <div key={title}><SurfaceIcon name={icon}/><b><LocalizedContent value={title}/></b><small><LocalizedContent value={note}/></small></div>)}/></div><p><LocalizedContent value={"Business leaders own the goals."}/><br /><LocalizedContent value={"The transformation team makes change repeatable."}/></p></div>; }
function PromptComposer() { return <div className="deck-codex-example"><div className="deck-codex-label"><img src="/assets/infrastructure/logos/thesvg/codex.svg" alt=""/>Codex <span>WORKFLOW BUILD BRIEF</span></div><CodexComposer/><div className="deck-build-attachments"><span>delivery-policy.md</span><span>acceptance-cases.json</span></div><p><LocalizedContent value="Use Activepieces MCP. Build a draft, test the branches, and return the evidence for review."/></p></div>; }
function RepoVisual() { return <div className="deck-repo-shell"><div className="deck-repo-top"><span><svg viewBox="0 0 24 24" width="25" height="25" fill="currentColor"><path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/></svg><b><LocalizedContent value={"SpielOS"}/></b><i /><LocalizedContent value={"Company workspace"}/></span><small><LocalizedContent value={"ILLUSTRATIVE PRODUCT VIEW"}/></small></div><div className="os-workspace-tabs"><b><LocalizedContent value={"Overview"}/></b><span><LocalizedContent value={"Runs"}/></span><span><LocalizedContent value={"Memory"}/></span><span><LocalizedContent value={"Tools"}/></span><span><LocalizedContent value={"Evals"}/></span><em><LocalizedContent value={"\u25CF All systems ready"}/></em></div><div className="os-workspace-body"><aside className="os-workspace-sidebar"><small><LocalizedContent value={"COMPANY"}/></small><span><LocalizedContent value={"\u2311 Strategy & goals"}/></span><span className="selected"><LocalizedContent value={"\u25BE Departments"}/></span><span className="indent"><LocalizedContent value={"Support"}/></span><span className="indent"><LocalizedContent value={"Sales"}/></span><span className="indent"><LocalizedContent value={"Finance"}/></span><small><LocalizedContent value={"EXPLORER"}/></small><span><LocalizedContent value={"\u25BE company-os"}/></span><code><LocalizedContent value={"\u251C departments/"}/></code><code><LocalizedContent value={"\u2502 \u2514 support/"}/></code><code><LocalizedContent value={"\u2502 \u251C workflow.md"}/></code><code><LocalizedContent value={"\u2502 \u2514 evals.json"}/></code><code><LocalizedContent value={"\u251C harness/"}/></code><code><LocalizedContent value={"\u2514 artifacts/"}/></code></aside><div className="os-workspace-main"><div className="os-page-heading"><div><small><LocalizedContent value={"DEPARTMENT / SUPPORT"}/></small><strong><LocalizedContent value={"Customer resolution"}/></strong></div><span><LocalizedContent value={"+ New run"}/></span></div><div className="os-run-metrics"><div><small><LocalizedContent value={"COMPLETED"}/></small><b><LocalizedContent value={"184"}/></b><span><LocalizedContent value={"runs this week"}/></span></div><div><small><LocalizedContent value={"QUALITY SCORE"}/></small><b><LocalizedContent value={"0.96"}/></b><span><LocalizedContent value={"against defined criteria"}/></span></div><div><small><LocalizedContent value={"REVIEW QUEUE"}/></small><b><LocalizedContent value={"04"}/></b><span><LocalizedContent value={"exceptions need a person"}/></span></div></div><div className="os-run-list"><div><b><LocalizedContent value={"Recent runs"}/></b><span><LocalizedContent value={"View all \u2197"}/></span></div><LocalizedContent value={[['0184', 'Delivery exception', 'Complete', '2.84s'], ['0183', 'Refund eligibility', 'Review', '3.11s'], ['0182', 'Order status', 'Complete', '2.49s']].map(([id, title, status, time]) => <section key={id}><code><LocalizedContent value={"#"}/><LocalizedContent value={id}/></code><strong><LocalizedContent value={title}/></strong><em className={status === 'Review' ? 'review' : ''}><LocalizedContent value={status}/></em><small><LocalizedContent value={time}/></small></section>)}/></div><div className="os-harness-status"><SurfaceIcon name="shield"/><span><b><LocalizedContent value={"One harness. Shared controls."}/></b><small><LocalizedContent value={"Context loaded \u2192 tools approved \u2192 quality verified \u2192 trace saved"}/></small></span></div></div><aside className="os-inspector"><small><LocalizedContent value={"SELECTED RUN / 0184"}/></small><strong><LocalizedContent value={"Run inspector"}/></strong><div><span><LocalizedContent value={"CONTEXT"}/></span><b><LocalizedContent value={"Delivery policy"}/></b><b><LocalizedContent value={"Order #1042"}/></b><b><LocalizedContent value={"Escalation rules"}/></b></div><div><span><LocalizedContent value={"CONNECTED TOOLS"}/></span><Providers logos={['activepieces', 'python', 'langsmith-langchain']}/></div><div><span><LocalizedContent value={"ARTIFACT"}/></span><b><LocalizedContent value={"\u2713 reply.md"}/></b><small><LocalizedContent value={"Verified \u00B7 ready for review"}/></small></div></aside></div><footer className="os-statusbar"><span><LocalizedContent value={"\u25CF Context synced"}/></span><span><LocalizedContent value={"Harness ready"}/></span><span><LocalizedContent value={"Every run is inspectable"}/></span></footer></div>; }
function ScaleVisual() { return <div className="deck-scale-visual"><svg viewBox="0 0 570 225" aria-hidden="true"><path d="M285 55 V90 M285 90 H85 V130 M285 90 V130 M285 90 H485 V130"/></svg><div className="deck-scale-source"><SurfaceIcon name="check-circle"/><b><LocalizedContent value={"One proven workflow"}/></b></div><div className="deck-scale-departments"><LocalizedContent value={[['Support', 'support'], ['Sales', 'group'], ['Finance', 'receipt']].map(([label, icon]) => <div key={label}><SurfaceIcon name={icon}/><b><LocalizedContent value={label}/></b><small><LocalizedContent value={"Adapt to the work"}/></small></div>)}/></div><div className="deck-outcome-line"><LocalizedContent value={"Shared infrastructure. Compounding capability."}/></div></div>; }
function ProductUI({ node }: {
    node: Tile;
}) {
    if (node.id === 'trace')
        return <LangSmithSurface />;
    if (node.id === 'evals')
        return <LangSmithSurface mode="evals"/>;
    if (node.id === 'observability')
        return <LangSmithSurface mode="monitor"/>;
    if (node.id === 'metrics')
        return <div className="deck-metrics"><div className="deck-example-label"><span><LocalizedContent value={"BUSINESS SCORECARD"}/></span><b><LocalizedContent value={"Baseline \u2192 pilot target"}/></b></div><LocalizedContent value={[['12 → ≤6 min', 'handling time', 'history'], ['$8 → ≤$6', 'cost per resolution', 'trending-up'], ['≥95%', 'quality acceptance', 'shield']].map(([value, text, icon]) => <div key={text}><SurfaceIcon name={icon}/><span><b><LocalizedContent value={value}/></b><small><LocalizedContent value={text}/></small></span><strong><LocalizedContent value={'TARGET'}/></strong></div>)}/><footer><LocalizedContent value={"Proposed pilot · business results pending. Passed build tests alone do not prove ROI."}/></footer></div>;
    const evals = node.id === 'evals';
    const rows = evals ? ['Answer supported by source', 'Relevant to the request', 'Company policy respected', 'Task completed successfully'] : ['Load customer and policy context', 'Reason about the request', 'Retrieve the order status', 'Validate the proposed response', 'Record result and artifacts'];
    return <div className="deck-product"><div className="deck-product-bar"><span><i /><LocalizedContent value={evals ? 'QUALITY GATES' : 'SUPPORT / RESOLUTION'}/></span><small><LocalizedContent value={"Illustrative run"}/></small></div><LocalizedContent value={rows.map((r, i) => <div className={`deck-trace-row ${evals ? 'deck-trace-row--eval' : ''}`} key={r}><span className="deck-trace-index"><LocalizedContent value={"0"}/><LocalizedContent value={i + 1}/></span><span><LocalizedContent value={r}/></span><LocalizedContent value={!evals && <span className="deck-trace-span" style={{ '--span-width': `${38 + i * 10}%`, '--span-start': `${i * 6}%` } as CSSProperties}/>}/><span className="deck-status"><LocalizedContent value={evals ? 'Pass' : '✓'}/></span></div>)}/><div className="deck-product-footer"><SurfaceIcon name={evals ? 'shield' : 'link'}/><span><LocalizedContent value={evals ? 'Custom criteria for this workflow' : 'Every action connects to a business result'}/></span></div></div>;
}
function TicketSteps({ node }: {
    node: Tile;
}) { return <ol className="deck-ticket-steps"><LocalizedContent value={node.rows?.map((row, i) => <li key={row} className={row === 'Human review / Send' ? 'deck-ticket-branch' : ''}><LocalizedContent value={row === 'Human review / Send' ? <div className="deck-confidence-branch"><svg viewBox="0 0 400 35" aria-hidden="true"><path d="M200 0 V10 Q200 16 190 16 H90 V35 M200 10 Q200 16 210 16 H310 V35"/></svg><span><SurfaceIcon name="group"/><LocalizedContent value={"Human review"}/></span><span><SurfaceIcon name="check-circle"/><LocalizedContent value={"Send"}/></span></div> : <><span className="deck-step-number"><LocalizedContent value={String(i + 1).padStart(2, '0')}/></span><b><LocalizedContent value={row}/></b></>}/></li>)}/></ol>; }
function PrimitiveBody({ node }: {
    node: Tile;
}) {
    if (node.id === 'value')
        return <ValueVisual />;
    if (node.id === 'layers')
        return <WorkLayersVisual />;
    if (node.id === 'goal')
        return <GoalVisual />;
    if (spec[node.id])
        return <Spec rows={spec[node.id]}/>;
    if (node.id === 'friction')
        return <FrictionVisual />;
    if (node.id === 'runtime')
        return <RuntimeVisual />;
    if (['procedural', 'semantic', 'episodic'].includes(node.id))
        return <MemoryVisual id={node.id}/>;
    if (node.id === 'director')
        return <DirectorVisual />;
    if (node.id === 'scale')
        return <ScaleVisual />;
    if (node.id === 'workflow') return <Spec rows={[["Impact × volume", 'Frequent delivery exceptions consume team capacity'], ['Readiness × risk', 'Order data exists · policy is clear · review is possible'], ['Prioritized backlog', 'Delivery exceptions → owner + acceptance brief']]}/>;
    if (node.id === 'process')
        return <WorkflowVisual process={node.id === 'process'}/>;
    if (['workers', 'departments', 'research', 'guardrails', 'outcomes'].includes(node.id))
        return <CapabilityGrid id={node.id}/>;
    if (['builder', 'episode', 'engineering', 'analysis', 'current', 'redesign', 'parallel'].includes(node.id))
        return <BuildPipeline id={node.id}/>;
    if (node.id === 'prompt')
        return <PromptComposer />;
    if (node.id === 'repo')
        return <RepoVisual />;
    if (node.id === 'context')
        return <Spec rows={[["The request", 'Customer, order and conversation'], ['The knowledge', 'Delivery status and approved policy'], ['The boundaries', 'Available tools and escalation rules']]}/>;
    if (node.id === 'support')
        return <Spec rows={[["First workflow", "Delivery exceptions · prove the result"], ["Next workflows", "Returns and refunds · reuse the controls"], ["Department system", "One owner · shared policies · measured outcomes"]]}/>;
    if (node.id === 'providers' || node.id === 'execution')
        return <div className="deck-provider-catalog"><span className="deck-eyebrow"><LocalizedContent value={"MODELS \u00B7 AGENTS \u00B7 AUTOMATION \u00B7 CODE"}/></span><Providers logos={node.logos || []}/><p><LocalizedContent value={"The operating system coordinates."}/><br /><LocalizedContent value={"Your preferred tools execute."}/></p></div>;
    return <Rows node={node}/>;
}
function Rows({ node }: {
    node: Tile;
}) { return node.rows ? <ul><LocalizedContent value={node.rows.map(row => <li key={row}><span className="deck-row-bullet"/><LocalizedContent value={row}/></li>)}/></ul> : node.note ? <p><LocalizedContent value={node.note}/></p> : null; }
export default function ComponentSurface({ node, kind }: {
    node: Tile;
    kind?: string;
}) {
    if(node.id==='thesis-overview')return <article className="deck-composition" data-node={node.id} style={{left:node.x,top:node.y,width:node.w,height:node.h}}><ThesisAssembly/></article>;
    if(node.id.startsWith('example-'))return <article className="deck-composition deck-example" data-node={node.id} style={{left:node.x,top:node.y,width:node.w,height:node.h}}><div className={node.id==='example-123'?'deck-example-full':'deck-example-scale'}><PracticalSurface focused={node.id!=='example-123'} mode={compactDetails[Number(node.id.replace('example-',''))].mode}/></div></article>;
    if (node.id.endsWith('-composition'))
        return <article className="deck-composition" data-node={node.id} style={{ left: node.x, top: node.y, width: node.w, height: node.h }}><LocalizedContent value={kind === 'team' ? <TeamAssembly /> : kind === 'harness' ? <HarnessAssembly /> : <MemoryAssembly />}/></article>;
    const primitive = !kind || kind === 'thesis', dashboard = kind === 'dashboard';
    const system = node.id === 'os', company = node.id === 'company', provider = node.id === 'providers';
    const roleMethods: Record<string, string[]> = { research: ['Use cases', 'Architecture', 'Standards'], analysis: ['Process map', 'Opportunity', 'ROI'], engineering: ['Agents', 'Workflows', 'Integrations'], observability: ['Traces', 'Quality', 'Impact'] };
    return <article className={`deck-tile ${primitive ? 'deck-tile--hero' : ''} ${system ? 'deck-tile--system' : ''} ${company ? 'deck-tile--context' : ''} ${provider ? 'deck-tile--providers' : ''} ${dashboard ? 'deck-tile--product' : ''}`} data-node={node.id} data-guide-node={node.id} style={{ left: node.x, top: node.y, width: node.w, height: node.h, '--tile-tone': `var(--${node.tone || 'primary'})` } as CSSProperties}>
        <header><span className="deck-icon"><SurfaceIcon name={node.icon}/></span><div><LocalizedContent value={management.includes(node.id) && <small><LocalizedContent value={"0"}/><LocalizedContent value={management.indexOf(node.id) + 1}/><LocalizedContent value={" / MANAGEMENT"}/></small>}/><strong><LocalizedContent value={node.title}/></strong><LocalizedContent value={system && <small><LocalizedContent value={"THE SHARED INTELLIGENCE LAYER"}/></small>}/></div></header>
        <LocalizedContent value={dashboard ? <ProductUI node={node}/> : system ? <SystemGrid /> : company ? <ContextCells /> : primitive ? <PrimitiveBody node={node}/> : kind === 'repository' ? <PrimitiveBody node={node}/> : kind === 'management' && node.id.endsWith('-inputs') ? <ManagementInput node={node}/> : kind === 'workflow' && ['old', 'new'].includes(node.id) ? <TicketSteps node={node}/> : <Rows node={node}/>}/>
        <LocalizedContent value={primitive && node.file && <footer className="deck-artifact"><SurfaceIcon name="file"/><span><LocalizedContent value={node.file}/></span><small><LocalizedContent value={"A recorded decision, ready for the next step"}/></small></footer>}/>
        <LocalizedContent value={kind === 'management' && node.file && <div className="deck-management-record"><span><LocalizedContent value={node.file}/></span><img src={`/assets/infrastructure/logos/thesvg/${node.id === 'act' ? 'trello' : 'notion'}.svg`} alt={node.id === 'act' ? 'Trello' : 'Notion'}/></div>}/>
        <LocalizedContent value={kind === 'team' && roleMethods[node.id] && <div className="deck-role-methods"><LocalizedContent value={roleMethods[node.id].map(tag => <span key={tag}><LocalizedContent value={tag}/></span>)}/></div>}/>
        <LocalizedContent value={!primitive && !dashboard && node.logos && <Providers logos={node.logos}/>}/>
    </article>;
}
