import content from './slides.json';
export const chapterOpenings = [
    ['How can a company use AI?', 'Start with the business objective, then understand how work gets done.', 'use AI?'],
    ['The management framework.', 'Goal → Observe → Decide → Act → Evaluate.', 'framework.'],
    ['The transformation team.', 'The people who design, build and improve the company’s AI systems.', 'team.'],
    ['SpielOS. The company OS.', 'Your company context, harness, memory and tools in one operating system.', 'company OS.'],
    ['Inside the AI harness.', 'Follow one prompt through context, the runtime, tools and guardrails.', 'AI harness.'],
    ['A company that remembers.', 'Keep the knowledge, methods and lessons that make the next run better.', 'remembers.'],
    ['Redesign the work.', 'Start with the business process. Choose the technology after.', 'work.'],
    ['Prove it. Then scale it.', 'Turn individual wins into a capability the whole company can use.', 'scale it.'],
    ['Observability & Evals.', 'Trace every run. Evaluate its quality. Measure its business impact.', 'Evals.'],
    ['The AI-first organization.', 'A company with the ability to keep improving how work happens.', 'AI-first organization.'],
];
// Executive narrative, kept separate from the underlying public content inventory.
const narrative: Record<number, [string, string, string?]> = {
    1: ['Start with the business objective.', 'Use AI to create more value: increase capacity, improve quality and lower the cost of getting work done.', 'business objective.'],
    2: ['Ask how work gets done.', 'Tasks are individual actions. Workflows connect them. Systems make the whole way of working repeatable.', 'how work gets done.'],
    3: ['Choose one valuable workflow.', 'Start with a recurring business problem, redesign the work and prove the result before expanding.', 'valuable workflow.'],
    4: ['Goal. Set the target.', '2× output at half the operating cost, one workflow at a time.', 'Goal.'],
    5: ['Observe. Follow the real work.', 'Gather facts, traces and feedback to see where time, money and quality are lost.', 'Observe.'],
    6: ['Decide. Choose the next change.', 'Use the evidence to prioritize an improvement and record the tradeoffs.', 'Decide.'],
    7: ['Act. Put the change to work.', 'Execute through the harness, workflows and tools, with people owning consequential decisions.', 'Act.'],
    8: ['Evaluate. Did it work?', 'Compare results with the goal, keep the lessons and feed the next cycle.', 'Evaluate.'],
    9: ['The management framework.', 'Goal → Observe → Decide → Act → Evaluate sits above the harness that executes the work.', 'management framework.'],
    10: ['There is a manager for the transformation.', 'Business analysis, agent engineering and observability connect priorities, system design and measurable outcomes.', 'manager for the transformation.'],
    11: ['Understand before automating.', 'Process analysts uncover how the work really happens and where a better design will matter.', 'Understand'],
    12: ['Design for the whole system.', 'Architecture makes context, models and tools work together toward a business result.', 'whole system.'],
    13: ['Turn a better idea into daily work.', 'Engineers build the agents, workflows and integrations that people can depend on.', 'daily work.'],
    14: ['Build Observability and Evals in.', 'The Evals engineer connects run traces, quality checks and business results from the start.', 'Observability and Evals'],
    15: ['One transformation team. Every department.', 'Business teams own their outcomes. The transformation team helps them continuously improve.', 'Every department.'],
    16: ['Your business is the context.', 'AI needs your strategy, policies, knowledge, people and systems to make useful decisions.', 'the context.'],
    17: ['SpielOS is the shared operating system.', 'The product brings context, memory, the harness, tools, guardrails and observability into one workspace.', 'SpielOS'],
    18: ['Same foundation. Different work.', 'Each department gets workflows, agents and measures designed for its own outcomes.', 'Different work.'],
    19: ['Keep the tools that work.', 'Connect your preferred models and platforms as execution providers inside one coherent system.', 'tools that work.'],
    20: ['Company context. SpielOS. Department systems.', 'One AI operating system connects your knowledge, harness and execution providers to business outcomes.', 'SpielOS.'],
    21: ['Every run starts with a prompt.', 'A prompt, task, trigger or event gives the harness a clear piece of work.', 'prompt.'],
    22: ['Brief the system before it acts.', 'Load the relevant request, knowledge, tools and boundaries for this task.', 'before it acts.'],
    23: ['The harness runs the agent loop.', 'The runtime reasons, calls tools and observes results until the task meets its completion criteria.', 'harness'],
    24: ['Give specialists the right work.', 'Delegate research, building, analysis and review when a dedicated worker can improve the result.', 'right work.'],
    25: ['Completion has a quality bar.', 'Check correctness, policy and required work before accepting the result.', 'quality bar.'],
    26: ['Every action leaves evidence.', 'Keep a trace of context, model calls, tools, timing, costs, errors and produced artifacts.', 'evidence.'],
    27: ['The harness turns prompts into verified work.', 'Context, runtime, tools, workers and guardrails form one observable execution loop.', 'verified work.'],
    28: ['Procedural memory knows how.', 'Procedural memory stores proven methods so the next run can reuse them.', 'how'],
    29: ['Semantic memory knows what.', 'Semantic memory keeps useful facts and knowledge available with their sources.', 'what'],
    30: ['Episodic memory remembers what happened.', 'Episodic memory captures past situations, decisions and outcomes worth learning from.', 'Episodic memory'],
    31: ['Give this task the right knowledge.', 'Retrieve what matters, leave out what does not and assemble a focused working context.', 'right knowledge.'],
    32: ['Turn experience into an advantage.', 'Review useful traces, retain the lesson and update the facts or methods that future work will use.', 'an advantage.'],
    33: ['The next run starts better informed.', 'Methods, facts and experience feed the work; the result adds another useful lesson.', 'better informed.'],
    34: ['A workflow delivers a business result.', 'Define the input, decisions, actions and outcome before choosing the technology.', 'business result.'],
    35: ['Map the work people actually do.', 'Identify the people, information, decisions and constraints behind the current process.', 'actually do.'],
    36: ['A faster bad process is still bad.', 'Remove waste, clarify decisions and preserve human judgment before you automate.', 'still bad.'],
    37: ['Choose the right way to execute.', 'Use skills, agents, code, workflow tools, MCP connections, APIs or people where each is most effective.', 'right way'],
    38: ['Earn the right to replace it.', 'Run the new workflow beside the current process and prove quality on comparable work.', 'Earn the right'],
    39: ['From manual handoffs to measured results.', 'A customer support request becomes a connected workflow with checks, escalation and feedback.', 'measured results.'],
    40: ['One win becomes a team capability.', 'Combine proven workflows to change how a department handles an entire class of work.', 'team capability.'],
    41: ['Share the foundation. Adapt the work.', 'Departments use common infrastructure while keeping their own context, workflows and success measures.', 'Adapt the work.'],
    42: ['Scale what you can prove.', 'Expand a successful method into new workflows and departments, one measured step at a time.', 'can prove.'],
    43: ['Specialized teams. Shared intelligence.', 'Each department moves toward its own outcomes on one company-wide foundation.', 'Shared intelligence.'],
    44: ['You can only improve what you can see.', 'Make production work observable so every result can lead to a better decision.', 'can see.'],
    45: ['The trace explains what happened.', 'Follow the run from its initial context through every action to its final artifact.', 'what happened.'],
    46: ['Evals tell us: was it good?', 'Test correctness, relevance, policy and task success against explicit thresholds.', 'Evals'],
    47: ['The scorecard asks: did it matter?', 'Compare time, cost, quality and adoption with the business outcome you set out to improve.', 'did it matter?'],
    48: ['Trace → Evaluate → Learn → Improve.', 'Observability feeds Observe; Evals and business outcomes feed Evaluate.', 'Improve.'],
    49: ['Build the ability to keep improving.', 'An AI-first company can continuously redesign its work while retaining control, knowledge and accountability.', 'keep improving.'],
    51: ['The OS becomes a product surface.', 'Context, execution and evidence meet in one inspectable workspace.', 'product surface.'],
    50: ['One workflow at a time.', 'The management framework, the transformation team and SpielOS make the next cycle better: Goal → Observe → Decide → Act → Evaluate.', 'One workflow'],
};
export type StorySlide = { id: number; concept: number; chapter: number; title: string; line: string; assembly: boolean; intro: boolean };
export const storySlides: StorySlide[] = content.flatMap((slide, i) => {
    const copy = narrative[slide.id];
    const beat = { ...slide, title: copy[0], line: copy[1], concept: slide.id, assembly: !!slide.assembly, intro: false };
    if (i === 0 || content[i - 1].chapter !== slide.chapter) { const opening = chapterOpenings[slide.chapter]; return [{ ...beat, concept: 0, title: opening[0], line: opening[1], assembly: false, intro: true }, beat]; }
    if (slide.id === 20) return [beat, { ...beat, concept: 51, title: narrative[51][0], line: narrative[51][1], assembly: true }];
    return [beat];
}).map((slide, i) => ({ ...slide, id: i + 1 }));
export const titleOverrides: Record<number, string> = {};
export const emphases: Record<number, string> = Object.fromEntries(Object.entries(narrative).map(([id, copy]) => [id, copy[2] || '']));
