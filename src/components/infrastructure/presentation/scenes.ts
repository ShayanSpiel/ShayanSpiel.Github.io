import {compactDetails} from './compact-story';
export type Tile = {
    id: string;
    title: string;
    icon: string;
    tone?: string;
    note?: string;
    rows?: string[];
    file?: string;
    logos?: string[];
    x: number;
    y: number;
    w: number;
    h: number;
};
export type Edge = [
    string,
    string,
    string?,
    string?
];
export type Scene = {
    tiles: Tile[];
    edges: Edge[];
    kind?: string;
};
export const chapters = ['The thesis', 'Management', 'Transformation team', 'Company architecture', 'Inside the harness', 'Memory & learning', 'Process to workflow', 'Scale to departments', 'Observability & evals', 'The AI-first organization'];
export const definitions: Record<string, Omit<Tile, 'id' | 'x' | 'y' | 'w' | 'h'>> = {
    value: { title: 'Business value', icon: 'target-lock', tone: 'primary', note: 'Start with the outcome the company needs.' },
    layers: { title: 'How work gets done', icon: 'layers', tone: 'accent', note: 'Tasks → workflows → systems.' },
    friction: { title: 'A customer is waiting.', icon: 'message-square', tone: 'warning', note: 'The work is simple. The handoffs are not.' },
    scale: { title: 'Prove it. Then multiply it.', icon: 'sitemap', tone: 'primary' },
    operations: { title: 'Operations', icon: 'cog', tone: 'primary', rows: ['Workflow automation', 'Resource planning', 'Cross-team execution'] },
    hr: { title: 'HR', icon: 'group', tone: 'accent', rows: ['Onboarding', 'Employee experience', 'People operations'] },
    workflow: { title: 'Resolve a customer request', icon: 'support', note: 'One owner. One measurable outcome.', tone: 'primary' },
    outcomes: { title: 'Better business outcomes', icon: 'trending-up', rows: ['Faster execution', 'Lower operating cost', 'Higher quality'] },
    goal: { title: 'Goal', icon: 'target-lock', tone: 'primary', note: 'Define what success looks like.', file: 'goal.md' },
    observe: { title: 'Observe', icon: 'bar-chart-alt-2', tone: 'success', note: 'Collect signals, traces and metrics.', file: 'observations.md' },
    decide: { title: 'Decide', icon: 'brain', tone: 'accent', note: 'Prioritize and plan the next change.', file: 'decisions.md' },
    act: { title: 'Act', icon: 'bolt', tone: 'warning', note: 'Execute with agents, tools and workflows.', file: 'tasks.md' },
    evaluate: { title: 'Evaluate', icon: 'check-circle', tone: 'primary', note: 'Measure results. Capture what worked.', file: 'evaluation.md' },
    'goal-inputs': { title: 'Goal inputs', icon: 'target-lock', rows: ['Business objectives', 'Success criteria', 'Stakeholders & constraints'] },
    'observe-inputs': { title: 'Observe inputs', icon: 'search', rows: ['Traces & metrics', 'Evals & feedback', 'Business outcomes'] },
    'decide-inputs': { title: 'Decision inputs', icon: 'brain', rows: ['Observations', 'Evaluation results', 'Priorities, risks & ROI'] },
    'evaluate-inputs': { title: 'Evaluation inputs', icon: 'check-circle', rows: ['Results vs. targets', 'Lessons learned', 'Next cycle & artifacts'] },
    improve: { title: 'Continuous improvement', icon: 'layers', note: 'Every cycle makes the next one better.' },
    director: { title: 'Manager', icon: 'group', note: 'Priorities · Architecture · Outcomes' },
    analysis: { title: 'Business analysts', icon: 'search', tone: 'success', note: 'Understand the real work.', logos: ['notion', 'trello'] },
    research: { title: 'AI systems & architecture', icon: 'layers', tone: 'accent', note: 'Choose patterns, models and tools.', logos: ['openai-chatgpt', 'claude-code'] },
    engineering: { title: 'Agent engineers', icon: 'code-alt', tone: 'warning', note: 'Build production systems.', logos: ['codex', 'n8n', 'python'] },
    observability: { title: 'Evaluation & observability', icon: 'bar-chart-alt-2', tone: 'primary', note: 'Connect AI quality to business results.', logos: ['langfuse', 'langsmith-langchain'] },
    company: { title: 'Company context', icon: 'building', rows: ['Strategy · Policies · Processes', 'Knowledge · People · Systems', 'Data · APIs'] },
    os: { title: 'AI Operating System', icon: 'layers', rows: ['Context · Memory · Harness', 'Tools · Guardrails · Observability'], note: 'The shared intelligence layer' },
    repo: { title: 'The OS is inspectable', icon: 'folder-open', tone: 'accent', note: 'Public reference structure for the product surface.' },
    departments: { title: 'Department systems', icon: 'group', rows: ['Sales · Support · Marketing', 'Finance · Operations · HR'], note: 'Different work. Shared foundation.' },
    providers: { title: 'Execution providers', icon: 'plug', logos: ['openai-chatgpt','codex','claude-code','opencode','activepieces','n8n','zapier','python'], note: 'Use the tools you already have.' },
    prompt: { title: 'Work arrives', icon: 'message-square', rows: ['Prompt · Task · Trigger · Event'] },
    context: { title: 'Context', icon: 'file', note: 'Only what this piece of work needs.' },
    runtime: { title: 'LLM / Agent loop', icon: 'brain', tone: 'accent', rows: ['Reason → Use tools → Observe', 'Repeat until the work is complete'] },
    workers: { title: 'Tools & Workers', icon: 'network-chart', tone: 'warning', rows: ['Research · Build · Analyze · Review'] },
    guardrails: { title: 'Guardrails', icon: 'shield', tone: 'success', note: 'Validate safety, quality and completion.' },
    result: { title: 'Result', icon: 'check-circle', note: 'Valid, complete work.' },
    trace: { title: 'Trace', icon: 'pulse', rows: ['Context · Model · Tool · Worker', 'Latency · Errors · Cost · Artifacts'] },
    procedural: { title: 'How we do the work', icon: 'book-open', tone: 'warning', rows: ['Skills · Playbooks · Procedures', 'Templates · Proven methods'] },
    semantic: { title: 'What we know', icon: 'data', tone: 'success', rows: ['Facts · Concepts · Company knowledge', 'Domain information'] },
    episodic: { title: 'What happened last time', icon: 'history', tone: 'accent', rows: ['Runs · Decisions · Outcomes', 'Important past events'] },
    builder: { title: 'Context builder', icon: 'filter', rows: ['Retrieve → Filter → Compose → Inject'] },
    sources: { title: 'Context sources', icon: 'file', rows: ['Company · Session · Files', 'Memory · Tool schemas'] },
    episode: { title: 'Episode summary', icon: 'history', note: 'Keep what makes future work better.' },
    process: { title: 'Business process', icon: 'network-chart', rows: ['People → Information → Decisions', 'Constraints → Outcome'] },
    current: { title: 'Current work', icon: 'search', rows: ['Who does what?', 'With which information?', 'Under which constraints?'] },
    redesign: { title: 'Redesigned process', icon: 'git-branch', rows: ['Remove waste', 'Define decisions', 'Preserve human judgment'] },
    execution: { title: 'Choose the execution', icon: 'plug', logos: ['codex', 'claude-code', 'python', 'n8n'], note: 'Skills · Agents · Code · APIs · Humans' },
    parallel: { title: 'Prove before replacing', icon: 'check-shield', rows: ['Current process ↔ New workflow', 'Compare quality and outcomes'] },
    old: { title: 'Manual process', icon: 'user', rows:['Ticket','Human reads','Search documents','Write response','Ask manager','Reply'] },
    new: { title: 'AI-assisted workflow', icon: 'network-chart', tone: 'success', rows:['Ticket','Classify','Retrieve knowledge','Agent draft','Confidence gate','Human review / Send','Log outcome'], logos: ['codex', 'python', 'n8n'] },
    production: { title: 'Measured production', icon: 'bar-chart-alt-2', rows: ['Quality · Cost · Time', 'Continuous monitoring', 'Improve the next run'] },
    sales: { title: 'Sales', icon: 'group', tone: 'primary', rows: ['Lead research', 'Qualification', 'Outreach · Deal support'], logos: ['salesforce'] },
    support: { title: 'Support', icon: 'support', tone: 'success', rows: ['Ticket triage', 'Knowledge search', 'Resolution · Escalation'], logos: ['zendesk'] },
    marketing: { title: 'Marketing', icon: 'trending-up', tone: 'accent', rows: ['Research · Content', 'Campaigns · Assets'], logos: ['claude-code', 'n8n'] },
    finance: { title: 'Finance', icon: 'receipt', tone: 'warning', rows: ['Invoice processing', 'PO matching · Approval', 'Reporting'], logos: ['python'] },
    evals: { title: 'Evaluation', icon: 'check-shield', tone: 'success', rows: ['Correctness · Relevance', 'Safety · Task success', 'Custom criteria'] },
    metrics: { title: 'Business metrics', icon: 'trending-up', tone: 'warning', rows: ['Time · Cost · Quality', 'Adoption · Business outcomes'] },
    learn: { title: 'Learn & improve', icon: 'refresh', tone: 'accent', note: 'Feed the next management cycle.' },
};
function tile(id: string, x: number, y: number, w = 250, h = 130): Tile { return { id, ...definitions[id], x, y, w, h }; }
const primitives = ['value', 'layers', 'workflow', 'goal', 'observe', 'decide', 'act', 'evaluate', '', 'director', 'analysis', 'research', 'engineering', 'observability', '', 'company', 'os', 'departments', 'providers', '', 'prompt', 'context', 'runtime', 'workers', 'guardrails', 'trace', '', 'procedural', 'semantic', 'episodic', 'builder', 'episode', '', 'process', 'current', 'redesign', 'execution', 'parallel', '', 'support', 'departments', 'scale', '', 'observability', 'trace', 'evals', 'metrics', '', 'os', ''];
// Exact circular paths: every arc uses the same radius in both axes.
function circleScene(ids: string[], cx: number, cy: number, radius: number, w: number, h: number): {tiles: Tile[]; edges: Edge[]} {
    const point = (degrees: number) => ({ x: cx + radius * Math.cos(degrees * Math.PI / 180), y: cy + radius * Math.sin(degrees * Math.PI / 180) });
    const angles = ids.map((_, i) => -90 + i * 360 / ids.length);
    const tiles = ids.map((id, i) => { const p = point(angles[i]); return tile(id, p.x - w / 2, p.y - h / 2, w, h); });
    const inside = (p: {x:number;y:number}, t:Tile) => p.x > t.x-8 && p.x < t.x+t.w+8 && p.y > t.y-8 && p.y < t.y+t.h+8;
    const edges:Edge[] = ids.map((id, i) => {
        const next = (i+1)%ids.length, end = angles[i] + 360/ids.length;
        let startAngle=angles[i], endAngle=end;
        while (inside(point(startAngle),tiles[i])) startAngle+=.25;
        while (inside(point(endAngle),tiles[next])) endAngle-=.25;
        const a=point(startAngle),b=point(endAngle);
        return [id,ids[next],'circle',`M ${a.x} ${a.y} A ${radius} ${radius} 0 0 1 ${b.x} ${b.y}`];
    });
    return {tiles,edges};
}
export function sceneFor(id: number): Scene {
 if(id===123)return {tiles:[{id:`example-${id}`,title:"",icon:"",x:0,y:0,w:1440,h:650}],edges:[],kind:"activepieces"};
 if(compactDetails[id])return {tiles:[{id:`example-${id}`,title:"",icon:"",x:230,y:0,w:660,h:460}],edges:[]};
    if (id === 9) {
        const ring=circleScene(['goal','observe','decide','act','evaluate'],750,330,258,236,130);
        const inputs=[tile('goal-inputs',0,30,272,260),tile('evaluate-inputs',0,350,272,260),tile('observe-inputs',1228,30,272,260),tile('decide-inputs',1228,350,272,260)];
        const inputEdges:Edge[]=inputs.map(input=>{
            const target=ring.tiles.find(t=>t.id===input.id.replace('-inputs',''))!;
            const right=input.x<target.x, sx=right?input.x+input.w:input.x, sy=input.y+input.h/2, tx=right?target.x:target.x+target.w, ty=target.y+target.h/2;
            const bend=right?330:1180, dx=right?1:-1, dy=ty>sy?1:-1;
            return [input.id,target.id,'annotation',`M ${sx} ${sy} H ${bend-dx*18} Q ${bend} ${sy} ${bend} ${sy+dy*18} V ${ty-dy*18} Q ${bend} ${ty} ${bend+dx*18} ${ty} H ${tx}`];
        });
        return {kind:'management',tiles:[...ring.tiles,tile('improve',650,255,200,155),...inputs],edges:[...ring.edges,...inputEdges]};
    }
    if(id===15)return {kind:'team',tiles:[{id:'team-composition',title:'Transformation team',icon:'group',x:0,y:0,w:1500,h:770}],edges:[]};
    if(id===50)return {kind:'finale',tiles:[tile('director',0,0,1500,70),tile('os',170,118,1160,220),...['sales','support','marketing','finance','operations'].map((id,i)=>tile(id,i*307,388,272,170)),tile('providers',0,608,1500,70),tile('outcomes',0,728,1500,70)],edges:[['director','os'],...['sales','support','marketing','finance','operations'].map(d=>['os',d] as Edge),...['sales','support','marketing','finance','operations'].map(d=>[d,'providers'] as Edge),['providers','outcomes']]};
    if(id===20||id===43)return {kind:'architecture',tiles:[tile('company',0,0,1500,100),tile('os',170,150,1160,230),...['sales','support','marketing','finance','operations'].map((id,i)=>tile(id,i*307,430,272,180)),tile('providers',0,660,1500,78)],edges:[['company','os'],...['sales','support','marketing','finance','operations'].map(d=>['os',d] as Edge),...['sales','support','marketing','finance','operations'].map(d=>[d,'providers'] as Edge)]};
    if(id===51)return {kind:'repository',tiles:[tile('repo',40,0,1420,580)],edges:[]};
    if(id===27)return {kind:'harness',tiles:[{id:'harness-composition',title:'Harness execution workspace',icon:'brain',x:0,y:0,w:1500,h:610}],edges:[]};
    if(id===33)return {kind:'memory',tiles:[{id:'memory-composition',title:'Memory and context workspace',icon:'data',x:0,y:0,w:1500,h:690}],edges:[]};
    if(id===39)return {kind:'workflow',tiles:[tile('old',0,0,385,625),tile('new',490,0,560,625),tile('production',1155,173,345,280)],edges:[['old','new'],['new','production']]};
    if(id===48){const ring=circleScene(['trace','evals','metrics','learn'],560,340,258,310,160);return {kind:'feedback',tiles:[...ring.tiles,tile('improve',480,255,160,170)],edges:ring.edges};}
    const key = primitives[id - 1] || 'workflow';
    if(id===21)return {tiles:[tile(key,230,-20,660,510)],edges:[]};
    if([14,26,44,45,46].includes(id)) return {tiles:[tile(key,85,-70,900,610)],edges:[],kind:'dashboard'};
    return {tiles:[tile(key,230,0,660,460)],edges:[],kind:[14,26,44,45,46,47].includes(id)?'dashboard':id===3||id===42?'thesis':undefined};
}
