# SpielOS Website Conversion and Content Rebuild Plan

Status: implemented on `website-conversion-rebuild`, pending final runtime evaluation

Purpose: give an implementation model enough product truth, exact copy, route decisions, SEO requirements, translation rules, and acceptance checks to complete the work without inventing a new strategy.

## 1. The outcome

Rebuild the public website around one clear path:

1. The visitor understands what SpielOS is.
2. The visitor sees that SpielOS runs its own company.
3. The visitor understands how the product works without needing technical knowledge.
4. The visitor sees the current commercial offer.
5. The visitor requests an Agent Brief for one repetitive workflow.

The website must make these three ideas work together:

1. **The Company Is the Product.** SpielOS is a real company running on SpielOS.
2. **The commercial result.** Target 2x the output at half the operating cost, one workflow at a time.
3. **The first client deliverable.** Every engagement starts with a clear Agent Brief.

Do not turn the site into a generic AI agency website. Do not hide the product architecture. Do not replace the Agent Brief with a discovery call, consultation, audit, lead magnet, or generic contact CTA.

## 2. Reader and writing contract

The canonical reader is defined only in `.agents/company/strategy/icp.md`.

Write for an owner, CEO, COO, or senior operator at an established online business. They already have customers and a working operation. Their team still does too much repetitive knowledge work by hand. They care about staff time, delivery speed, operating cost, capacity, missed details, slow responses, and errors.

They are not developers, agent builders, AI agencies, or people shopping for a harness to build themselves.

### English copy rules

- Use short, direct, conversational English.
- Start from recognizable work, not internal product terminology.
- Explain one idea per section.
- Prefer concrete verbs and specific nouns.
- Keep paragraphs to one to three sentences where possible.
- Use `Agent Brief` everywhere. Do not use `Agent Briefing`.
- Use `2x`, not `2X` or `2×`, in metadata and plain text for consistent search rendering.
- Product vocabulary may appear on `/architecture/`, but every term must be explained in buyer language.
- Do not use an em dash.
- Do not use these phrases: transform your business, unlock growth, supercharge, cutting-edge, revolutionary, seamless, AI-powered solutions, intelligent automation, future-proof, game-changing, tailored solutions, leverage AI, end-to-end transformation.
- Do not use theatrical formulas such as `This is not X. It is Y.` more than once on the entire site.
- Do not write unsupported autonomy, savings, throughput, reply-rate, or quality claims.
- The 2x output and half-cost statement is a target measured against the client's current baseline. It is not a guaranteed result.

### Persian copy rules

- Follow `.agents/skills/translation-fa/SKILL.md` and its `persian-glossary.md`.
- Translate the meaning and action, not English sentence structure.
- Use natural, modern, conversational Persian for an Iranian operator.
- Use `تو`, `رو`, and conversational verbs consistently.
- Use Persian digits in body copy.
- Use `ایجنت`, `دپارتمان`, `ورک‌فلو`, `تأیید`, and `اجرا` according to the glossary.
- Explain technical behavior before naming architecture.
- Do not introduce technical transliterations when ordinary Persian communicates the meaning.
- Review the Persian page without looking at the English source. Every sentence must stand on its own.

## 3. Fixed information architecture

Use this public navigation:

1. Services: `/services/`
2. Architecture: `/architecture/`
3. Live: `/live/`
4. Notes: `/notes/`
5. Founder: `/founder/`
6. Primary CTA: `Request an Agent Brief` to `/services/agent-brief/#request`

Keep `/contact/` as the general contact fallback. Keep it in the footer, not the primary navigation.

### Route roles

| Route | One job | Primary next step |
|---|---|---|
| `/` | Explain the category and route the visitor | Request an Agent Brief or see Live |
| `/services/` | Sell the current implementation service | Request an Agent Brief |
| `/services/agent-brief/` | Show the first deliverable and collect the lead | Submit one workflow |
| `/architecture/` | Explain how SpielOS operates a company | See Live or request an Agent Brief |
| `/live/` | Prove that the company runs on SpielOS | Request an Agent Brief |
| `/notes/` | Educate operators through useful evidence | Read a relevant note or visit Services |
| `/founder/` | Establish founder credibility | See the product or request an Agent Brief |
| `/contact/` | Receive general business inquiries | Submit a general message |

### Waitlist replacement decision

The owner approved replacing the legacy waitlist destination with Architecture.

- `/waitlist/` redirects directly to `/architecture/`.
- `/fa/waitlist/` redirects directly to `/fa/architecture/`.
- `src/components/showcase/*` remains protected and untouched so the former experience stays recoverable in Git history.
- New Architecture components live under `src/components/architecture/` and do not reuse the showcase implementation.

### Features migration

Do not maintain two competing architecture systems.

1. Build and verify `/architecture/` first.
2. Replace the `/features/` hub with one direct 301 redirect to `/architecture/` after the new page is complete.
3. Do not redirect every feature subpage blindly.
4. Before changing a feature subpage, classify it using Search Console impressions, backlinks, and current organic visits.
5. If a subpage has meaningful value, redirect it to the closest matching section or future page.
6. If it has no value, remove it from navigation and the sitemap, apply `noindex` while it remains available, then retire it in a later cleanup.
7. No redirect chains. No internal link may point to a redirect.

## 4. Conversion and click-depth contract

The meaning of every CTA must match what happens next.

| CTA label | Required behavior |
|---|---|
| Request an Agent Brief | Show the request form immediately or open `/services/agent-brief/#request` |
| See an Agent Brief | Open the real Agent Brief example |
| Explore the architecture | Open `/architecture/` |
| See SpielOS live | Open `/live/` |
| View system details | Reveal the technical record on `/live/` |
| Talk to Shayan | Open `/contact/` only when the visitor wants a general conversation |

Do not label a link `Request`, `Get`, or `Start` if it opens an explanation section.

### Maximum click depth

- From the homepage, Services, Architecture, Live, Founder, or the navigation, the Agent Brief form must be visible after one click.
- Form submission is the next action.
- A visitor may choose an educational path, but conversion must not require reading the educational modal first.

### Implementation pattern

Make `/services/agent-brief/#request` the canonical form destination.

On pages that include the shared modal, use a crawlable link with progressive enhancement:

```astro
<a href={localizePath("/services/agent-brief/#request", locale)} data-open-contact-modal>
  {t(locale, "cta.requestAgentBrief")}
</a>
```

If JavaScript works, the link may open the shared form modal. Without JavaScript, it must navigate to the inline form on the Agent Brief page. Do not use a button with no URL for the primary conversion path.

## 5. Homepage implementation

### Page purpose

Establish the category, connect it to a concrete business result, prove that SpielOS runs itself, and route visitors according to intent.

Do not turn the homepage into a duplicate Services page. Do not make the founder biography the entire first viewport. Preserve the strongest founder evidence in one compact section.

### SEO

- Search intent: branded discovery plus AI workflow systems for established businesses
- Title: `SpielOS | AI Workflow Systems for Established Businesses`
- Description: `SpielOS runs real company work through supervised AI departments. Start with one repetitive workflow and a clear Agent Brief.`
- Canonical: `https://spielos.xyz/`
- Schema: preserve accurate Person, WebSite, SoftwareApplication, and BreadcrumbList nodes only when all marked facts remain visible and true
- Primary internal links: Services, Architecture, Live, Agent Brief, Founder

### Section 1: Hero

Eyebrow:

> THE COMPANY IS THE PRODUCT

H1:

> SpielOS is an AI company running on SpielOS.

Body:

> We use SpielOS to run real company work through supervised AI Departments. Then we use the same system to replace repetitive workflows inside established businesses.

Supporting line:

> Start with one workflow. Build toward 2x the output at half the operating cost.

Primary CTA:

> Request an Agent Brief

Secondary CTA:

> See SpielOS live

Persian:

Eyebrow:

> خود شرکت، محصوله

H1:

> SpielOS یه شرکت AIـه که با خود SpielOS کار می‌کنه.

Body:

> ما کارهای واقعی شرکت رو با دپارتمان‌های AI و زیر نظر آدم‌ها روی SpielOS اجرا می‌کنیم. بعد از همین سیستم برای کم‌کردن کارهای تکراری داخل کسب‌وکارهای واقعی استفاده می‌کنیم.

Supporting line:

> از یک ورک‌فلو شروع کن. هدف اینه که خروجی رو ۲ برابر و هزینه عملیاتی رو نصف کنیم.

Primary CTA:

> Agent Brief خودت رو درخواست کن

Secondary CTA:

> SpielOS رو در حال کار ببین

### Section 2: Recognizable problem

Label:

> THE WORK

H2:

> Your team is doing the same important work again and again.

Body:

> Requests arrive. Someone gathers information, checks rules, updates tools, prepares an answer, and passes the work to the next person. The process works, but it consumes time, slows delivery, and makes growth more expensive.

Cards:

- Customer requests that need the same research and response steps
- Reports assembled by hand from several tools
- Intake, scheduling, triage, and follow-up work
- Delivery checks that depend on one busy operator

Persian H2:

> تیمت هر روز یک کار مهم رو بارها از اول انجام می‌ده.

Persian body:

> درخواست می‌رسه. یک نفر اطلاعات رو جمع می‌کنه، قوانین رو بررسی می‌کنه، چند ابزار رو به‌روز می‌کنه، جواب رو آماده می‌کنه و کار رو به نفر بعد می‌سپاره. کار جلو می‌ره، اما وقت تیم رو می‌گیره، تحویل رو کند می‌کنه و رشد رو گرون‌تر می‌کنه.

### Section 3: Product mechanism

Label:

> HOW SPIELOS WORKS

H2:

> One operating loop keeps the work moving and accountable.

Body:

> SpielOS gives the company a measurable Goal, observes the available evidence, chooses the next bounded action, acts through approved Connections, and evaluates the result. Reusable Departments carry the work without turning the company into one tangled automation.

Show the visual:

> GOAL -> OBSERVE -> DECIDE -> ACT -> EVALUATE

CTA:

> Explore the architecture

Persian H2:

> یک چرخه مشخص، کار رو جلو می‌بره و نتیجه رو قابل بررسی نگه می‌داره.

Persian body:

> SpielOS برای شرکت یک هدف قابل اندازه‌گیری تعریف می‌کنه، اطلاعات موجود رو بررسی می‌کنه، قدم بعدی رو انتخاب می‌کنه، از راه دسترسی‌های تأییدشده کار رو انجام می‌ده و نتیجه رو می‌سنجه. دپارتمان‌های قابل استفاده دوباره، کار رو پیش می‌برن بدون اینکه کل شرکت به یک اتوماسیون درهم تبدیل بشه.

### Section 4: Live proof

Label:

> LIVE PROOF

H2:

> This is the system running our company now.

Body:

> SpielOS coordinates our real goals, Departments, approvals, work records, and evaluations. The public Live page shows the current company view and the evidence behind it.

Do not show raw internal goal IDs in this homepage section. Show one current plain-language business goal and one meaningful status line sourced from live data.

CTA:

> See the live company

Persian H2:

> همین سیستم الان شرکت ما رو می‌چرخونه.

Persian body:

> SpielOS هدف‌های واقعی شرکت، دپارتمان‌ها، تأییدها، سابقه کار و ارزیابی نتیجه رو هماهنگ می‌کنه. صفحه Live وضعیت فعلی شرکت و مدرک پشت هر نتیجه رو نشون می‌ده.

### Section 5: Current commercial path

Label:

> START WITH ONE WORKFLOW

H2:

> We build the first system with you.

Body:

> We identify one repetitive workflow with a clear cost or capacity problem. We define it in an Agent Brief, build it on SpielOS, test it against real cases, and measure it against the way your team works today.

Primary CTA:

> Request an Agent Brief

Secondary CTA:

> See implementation services

Persian H2:

> اولین سیستم رو با هم می‌سازیم.

Persian body:

> یک ورک‌فلوی تکراری رو پیدا می‌کنیم که هزینه یا محدودیت ظرفیت مشخصی داره. اون رو در قالب Agent Brief تعریف می‌کنیم، روی SpielOS می‌سازیم، با نمونه‌های واقعی تست می‌کنیم و با روش فعلی تیمت مقایسه می‌کنیم.

### Section 6: Agent Brief

Label:

> YOUR FIRST DELIVERABLE

H2:

> The work starts with a clear Agent Brief.

Body:

> Before anything is built, we define the result, inputs, outputs, interface, required knowledge, rules, approvals, and success measure for one workflow. You keep the brief whether or not we work together.

Primary CTA:

> Request your Agent Brief

Secondary CTA:

> See an Agent Brief

Persian H2:

> کار با یک Agent Brief روشن شروع می‌شه.

Persian body:

> قبل از ساختن هر چیزی، نتیجه، ورودی‌ها، خروجی‌ها، محل تعامل آدم‌ها، اطلاعات مورد نیاز، قوانین، تأییدها و معیار موفقیت یک ورک‌فلو رو مشخص می‌کنیم. چه با هم کار کنیم چه نه، بریف برای تو می‌مونه.

### Section 7: Founder evidence

Keep one concise founder section. Reuse verified facts from `src/config.ts` and the existing founder page. Do not invent a new life story.

H2:

> Ten years of building systems led to one company system.

Body direction:

> Briefly connect Shayan's prior products and systems work to the reason SpielOS exists. End with a contextual link to `/founder/`. Keep this section under 120 English words.

CTA:

> Read Shayan's story

### Section 8: Notes

Feature only notes that help the canonical buyer understand repetitive work, implementation choices, quality, approvals, operating cost, or evidence. Do not feature builder tutorials, waitlist retrospectives, prompt experiments, or obsolete product architecture on the homepage.

### Section 9: Final CTA

H2:

> Which workflow keeps taking time from your team?

Body:

> Describe one repetitive process. I will review the opportunity and, if it is a good fit, map it into an Agent Brief with you.

CTA:

> Request an Agent Brief

Persian H2:

> کدوم ورک‌فلو هر هفته وقت تیمت رو می‌گیره؟

Persian body:

> یک فرآیند تکراری رو توضیح بده. فرصت رو بررسی می‌کنم و اگر مناسب باشه، با هم اون رو به یک Agent Brief روشن تبدیل می‌کنیم.

## 6. Architecture page implementation

### Page purpose

Explain the real architecture and why it makes company work more reliable. The page is product education, not a technical manual and not a generic glossary.

### SEO

- Search intent: understand how SpielOS coordinates AI work across a company
- Primary topic: AI company operating system architecture
- Title: `SpielOS Architecture | How an AI Company Runs`
- Description: `See how SpielOS turns company goals into supervised work through reusable departments, workflows, agents, connections, and evidence.`
- Canonical: `https://spielos.xyz/architecture/`
- Schema: BreadcrumbList. Add SoftwareApplication only if it does not duplicate or conflict with the homepage node and all properties are visibly supported.
- Required internal links: Services, Agent Brief, Live, relevant notes
- Required locale route: `/fa/architecture/`

### Section 1: Hero

Label:

> SPIELOS ARCHITECTURE

H1:

> One operating system for a company of AI Departments.

Body:

> SpielOS turns measurable company Goals into supervised work. Departments run repeatable Workflows, act through approved Connections, produce visible Artifacts, and improve through evaluation.

Primary CTA:

> See SpielOS running live

Secondary CTA:

> Map your first workflow

Persian H1:

> یک سیستم‌عامل برای شرکتی با دپارتمان‌های AI.

Persian body:

> SpielOS هدف‌های قابل اندازه‌گیری شرکت رو به کارهای قابل کنترل تبدیل می‌کنه. دپارتمان‌ها ورک‌فلوهای مشخص رو اجرا می‌کنن، از راه دسترسی‌های تأییدشده کار انجام می‌دن، نتیجه و مدرک می‌سازن و با ارزیابی بهتر می‌شن.

### Section 2: Operating loop

H2:

> Every part of the company runs through one loop.

Body:

> A Goal defines the result. SpielOS observes the available evidence, chooses the next bounded action, performs the work through approved Connections, and evaluates what happened before deciding what comes next.

Visual labels:

- Goal: define the result
- Observe: read the current evidence
- Decide: choose the next allowed action
- Act: perform the work
- Evaluate: compare the result with the goal

Persian H2:

> همه بخش‌های شرکت با یک چرخه کار می‌کنن.

Persian body:

> هدف مشخص می‌کنه چه نتیجه‌ای می‌خوایم. SpielOS اطلاعات موجود رو بررسی می‌کنه، قدم بعدی و مجاز رو انتخاب می‌کنه، کار رو از راه دسترسی‌های تأییدشده انجام می‌ده و قبل از تصمیم بعدی، نتیجه رو می‌سنجه.

### Section 3: Department composition

H2:

> Departments are reusable parts of the company.

Body:

> A Department owns one business capability, such as Outbound, Content, Customer Support, Research, or Operations. It can work independently or contribute to a larger company Goal. Departments coordinate without becoming one permanent, fragile workflow.

Visual requirement: show one Department assembled from Workflow, Agent, Skill, Connection, and Artifact blocks. The visual must show relationships, not seven unrelated cards.

Persian H2:

> دپارتمان‌ها اجزای قابل استفاده دوباره شرکت هستن.

Persian body:

> هر دپارتمان مسئول یک توانایی مشخص شرکت مثل ارتباط‌گیری برای فروش، محتوا، پشتیبانی مشتری، تحقیق یا عملیاته. می‌تونه مستقل کار کنه یا بخشی از یک هدف بزرگ‌تر شرکت رو جلو ببره. دپارتمان‌ها با هم هماهنگ می‌شن، بدون اینکه به یک ورک‌فلوی دائمی و شکننده تبدیل بشن.

### Section 4: System map

H2:

> The seven parts of a SpielOS company.

Use these definitions exactly unless product truth changes:

- **Goal:** the measurable result the company is pursuing.
- **Department:** a reusable business capability responsible for part of that result.
- **Workflow:** the repeatable path from input to completed work.
- **Agent:** a bounded role responsible for one part of the Workflow.
- **Skill:** a reusable method an Agent follows.
- **Connection:** approved access to email, CRM, analytics, or another external system.
- **Artifact:** the output and evidence the work produced.

Persian:

- **هدف:** نتیجه قابل اندازه‌گیری که شرکت دنبال می‌کنه.
- **دپارتمان:** یک توانایی قابل استفاده دوباره که مسئول بخشی از نتیجه است.
- **ورک‌فلو:** مسیر مشخص از ورودی تا کار کامل‌شده.
- **ایجنت:** یک نقش محدود که بخشی از ورک‌فلو رو انجام می‌ده.
- **مهارت:** روش قابل استفاده دوباره‌ای که ایجنت دنبال می‌کنه.
- **اتصال:** دسترسی تأییدشده به ایمیل، CRM، آنالیتیکس یا یک سیستم بیرونی دیگه.
- **خروجی و مدرک:** چیزی که کار تولید کرده و مدرکی که نشون می‌ده چه اتفاقی افتاده.

Note: the public English label remains `Artifact` because it is canonical product vocabulary. In general Persian explanation, lead with `خروجی و مدرک`. Do not force an unnatural transliteration.

### Section 5: Control and evidence

H2:

> The company stays under control while the work keeps moving.

Body:

> Important actions can wait for human approval. Connections limit where the system may act. Artifacts preserve the work and its evidence. Evaluation shows whether the result was useful, not only whether an Agent produced an answer.

Bullets:

- Persistent Goals that survive a chat session
- Human approval where judgment matters
- Controlled access to external systems
- Visible outputs and evidence
- Evaluation against the intended result
- Separate business experiments and system improvements

Persian H2:

> کار جلو می‌ره، اما کنترل شرکت دست آدم‌ها می‌مونه.

Persian body:

> کارهای مهم می‌تونن منتظر تأیید آدم بمونن. اتصال‌ها مشخص می‌کنن سیستم کجا اجازه عمل داره. خروجی‌ها و مدارک نگه داشته می‌شن. ارزیابی هم مشخص می‌کنه نتیجه واقعاً مفید بوده یا فقط یک جواب تولید شده.

### Section 6: Real example

H2:

> See one Department run from goal to result.

Use the real Outbound Department as the default example. Source all changing state from committed public data. Do not invent metrics.

- Goal: create qualified sales conversations.
- Observe: review the ICP, prospect evidence, delivery state, and remaining qualified queue.
- Decide: choose the next qualified prospects and permitted channel.
- Act: research, draft, approve, and deliver specific outreach.
- Evaluate: review delivery, replies, qualified conversations, and evidence quality.
- Artifacts: prospect research, message drafts, delivery records, and results.

CTA:

> See the live company record

Persian H2:

> اجرای یک دپارتمان رو از هدف تا نتیجه ببین.

### Section 7: Commercial bridge

H2:

> Start with one workflow inside your company.

Body:

> We identify one repetitive process, define its result and constraints in an Agent Brief, and build the working system on SpielOS.

CTA:

> Request your Agent Brief

Persian H2:

> از یک ورک‌فلو داخل شرکتت شروع کن.

Persian body:

> یک فرآیند تکراری رو پیدا می‌کنیم، نتیجه و محدودیت‌هاش رو در قالب Agent Brief مشخص می‌کنیم و سیستم کاری رو روی SpielOS می‌سازیم.

## 7. Services page implementation

### Page purpose

Sell one focused service: design and implementation of agent workflows on SpielOS. The product is the delivery system and proof. The Agent Brief is the first deliverable.

### SEO

- Search intent: hire someone to implement an AI workflow or agent system
- Primary topic: AI agent implementation services
- Title: `AI Agent Implementation Services | SpielOS`
- Description: `Turn one repetitive business workflow into a tested AI system. Start with a free Agent Brief that defines the result, controls, and success measure.`
- Canonical: `https://spielos.xyz/services/`
- Schema: Service plus localized BreadcrumbList. Provider references must resolve to the shared Person or Organization node.
- Required internal links: Agent Brief, Architecture, Live, Contact

### Section order

1. Result and scope
2. Agent Brief
3. From brief to working system
4. Good-fit workflows
5. Why SpielOS is different
6. Delivery process
7. Fit and exclusions
8. Final CTA

### Section 1: Hero

Label:

> AI AGENT IMPLEMENTATION

H1:

> 2x your output at half the cost, one workflow at a time.

Body:

> We identify one repetitive, expensive workflow, define it in an Agent Brief, and build a supervised AI system measured against the way your team works today.

Evidence note:

> The target is measured against your current output, quality, time, and operating cost. Results depend on the workflow and available data.

Primary CTA:

> Request an Agent Brief

Secondary CTA:

> See an Agent Brief

Persian H1:

> ۲ برابر خروجی با نصف هزینه، هر بار برای یک ورک‌فلو.

Persian body:

> یک ورک‌فلوی تکراری و پرهزینه رو پیدا می‌کنیم، اون رو در قالب Agent Brief تعریف می‌کنیم و یک سیستم AI قابل کنترل می‌سازیم که با روش فعلی تیمت مقایسه می‌شه.

Persian evidence note:

> هدف رو با خروجی، کیفیت، زمان و هزینه عملیاتی فعلی می‌سنجیم. نتیجه به نوع ورک‌فلو و اطلاعات موجود بستگی داره.

### Section 2: Agent Brief

H2:

> Your first deliverable is an Agent Brief.

Body:

> Before building anything, we define what the workflow must achieve, what it receives, what it produces, where people interact with it, what knowledge it needs, which rules and approvals constrain it, and how success will be measured.

Footer:

> You keep the brief whether or not we work together.

Primary CTA:

> Request your Agent Brief

Secondary CTA:

> See the complete example

Persian H2:

> اولین چیزی که تحویل می‌گیری، یک Agent Briefـه.

Persian body:

> قبل از ساختن هر چیزی مشخص می‌کنیم ورک‌فلو باید به چه نتیجه‌ای برسه، چه ورودی‌ای می‌گیره، چه خروجی‌ای می‌ده، آدم‌ها کجا باهاش در ارتباط هستن، به چه اطلاعاتی نیاز داره، چه قوانین و تأییدهایی محدودش می‌کنن و موفقیت چطور سنجیده می‌شه.

Persian footer:

> چه با هم کار کنیم چه نه، بریف برای تو می‌مونه.

### Section 3: From brief to system

H2:

> From Agent Brief to a working system.

Body:

> If the opportunity is strong, we design the workflow, connect the required systems, test it with real cases, set human approvals, deploy it, and compare the result with the current process.

Steps:

1. Map the current work and baseline.
2. Define the system, controls, and success measure.
3. Connect the required data and tools.
4. Test with real cases before launch.
5. Deploy, document, and measure the result.

Persian H2:

> Agent Brief رو به یک سیستم واقعی تبدیل می‌کنیم.

Persian body:

> اگر فرصت مناسبی باشه، ورک‌فلو رو طراحی می‌کنیم، سیستم‌های لازم رو وصل می‌کنیم، با نمونه‌های واقعی تست می‌کنیم، تأییدهای انسانی رو مشخص می‌کنیم، سیستم رو راه می‌اندازیم و نتیجه رو با فرآیند فعلی مقایسه می‌کنیم.

### Section 4: Good-fit workflows

H2:

> Start where repeated work already has a cost.

Use examples based on work, not industry cards:

- Customer intake and request triage
- Support research and response preparation
- Recurring reporting across several systems
- Scheduling, follow-up, and status updates
- Delivery checks and quality review
- Research that follows the same evidence process

Body:

> The best first workflow happens often, follows recognizable rules, uses accessible information, and has a result your team can measure.

Persian H2:

> از کاری شروع کن که تکرارش همین الان هم هزینه داره.

Persian body:

> بهترین ورک‌فلوی اول، کاریه که زیاد تکرار می‌شه، قوانین قابل تشخیص داره، اطلاعاتش در دسترسه و نتیجه‌ش برای تیم قابل اندازه‌گیریه.

### Section 5: Product proof

H2:

> Built on the same system running our company.

Body:

> SpielOS is how we coordinate our own Goals, Departments, Workflows, approvals, Connections, and evidence. Client systems use the same operating model, scoped to one valuable workflow first.

CTAs:

> Explore the architecture

> See SpielOS live

Persian H2:

> سیستم مشتری رو روی همون محصولی می‌سازیم که شرکت خودمون رو می‌چرخونه.

Persian body:

> SpielOS هدف‌ها، دپارتمان‌ها، ورک‌فلوها، تأییدها، اتصال‌ها و مدارک شرکت خودمون رو هماهنگ می‌کنه. سیستم مشتری هم با همین مدل ساخته می‌شه و از یک ورک‌فلوی ارزشمند شروع می‌کنه.

### Section 6: Fit and exclusions

H2:

> This works best when the business already works.

Good fit:

- You have real customers and an active operation.
- A recurring workflow consumes meaningful staff time.
- The result can be observed and compared.
- The required information and systems are accessible.
- You want a working implementation, not an AI idea workshop.

Not a fit:

- You are pre-revenue and still looking for a product idea.
- You want a general chatbot with no defined job.
- The work happens rarely or has no measurable result.
- You are looking for a builder toolkit to assemble yourself.

### Section 7: Final CTA

H2:

> Show me one workflow your team repeats every week.

Body:

> I will review the opportunity and, if it is suitable, map it into an Agent Brief with you.

CTA:

> Request an Agent Brief

Persian H2:

> یک ورک‌فلو رو نشونم بده که تیمت هر هفته تکرارش می‌کنه.

Persian body:

> فرصت رو بررسی می‌کنم و اگر مناسب باشه، با هم اون رو به یک Agent Brief روشن تبدیل می‌کنیم.

## 8. Agent Brief page and form

### Page purpose

Make the Agent Brief feel like a real, useful first deliverable. Show the complete framework and provide the request form inline. Preserve the existing seven-part framework. Do not make it more complex.

### SEO

- Search intent: understand or request an AI workflow assessment
- Title: `Free AI Workflow Assessment and Agent Brief | SpielOS`
- Description: `Map one repetitive workflow into a clear Agent Brief covering its result, inputs, outputs, controls, required knowledge, and success measure.`
- Canonical: `https://spielos.xyz/services/agent-brief/`
- Schema: Service or CreativeWork only if the visible content fully supports it. Do not add FAQ schema without a real visible FAQ.
- Required links: Services, Architecture, privacy information, Contact fallback

### Page hero

Label:

> AGENT BRIEF

H1:

> Define the workflow before building the system.

Body:

> In one focused assessment, we turn a repetitive process into a clear brief for the result, inputs, outputs, human touchpoints, required knowledge, rules, approvals, and success measure.

Primary CTA:

> Request your Agent Brief

Trust line:

> You keep the brief whether or not we work together.

Persian H1:

> قبل از ساختن سیستم، ورک‌فلو رو دقیق تعریف کن.

Persian body:

> در یک بررسی متمرکز، یک فرآیند تکراری رو به بریف روشنی برای نتیجه، ورودی‌ها، خروجی‌ها، محل دخالت آدم‌ها، اطلاعات مورد نیاز، قوانین، تأییدها و معیار موفقیت تبدیل می‌کنیم.

### Form location and behavior

- Add an inline form section with `id="request"`.
- Keep the form available without JavaScript.
- The shared modal may reuse the same form component and copy.
- Do not maintain two independent form implementations.
- Extract one shared `AgentBriefForm.astro` component used inline and in the modal.
- Preserve user input when submission fails.
- Show loading, error, and success states.
- Move focus into the modal when opened.
- Trap focus inside the open modal.
- Return focus to the triggering link after close.
- Close on Escape and overlay click.
- Give the close control a localized aria label.
- On mobile, keep the close control clear of title and description text.
- Do not use a circular wrapper for the success icon.

### Exact form copy

Title:

> Request your Agent Brief

Description:

> Tell me what your business does and describe one repetitive workflow. If it looks suitable, I will invite you to a free 30-minute assessment and turn it into a clear Agent Brief.

Fields:

1. `Name`
2. `Work email`
3. `Your business and workflow`

Textarea placeholder:

> Example: We run a travel marketplace. Our team manually handles about 80 booking-change requests a day across email and our CRM.

Helper text:

> Include your website, who handles the workflow now, how often it happens, and what a good result looks like.

Submit:

> Request my Agent Brief

Trust text:

> You keep the brief whether or not we work together. Your information is used only to review the workflow and reply.

Success title:

> Your workflow is in.

Success body:

> I will review what you sent. If the workflow looks suitable, I will email you to arrange the assessment.

Error:

> Your request was not sent. Your answers are still here. Try again or email me directly.

Persian title:

> Agent Brief خودت رو درخواست کن

Persian description:

> بگو کسب‌وکارت چه کاری انجام می‌ده و یک ورک‌فلوی تکراری رو توضیح بده. اگر فرصت مناسبی باشه، برای یک بررسی رایگان ۳۰ دقیقه‌ای دعوتت می‌کنم و اون رو به یک Agent Brief روشن تبدیل می‌کنیم.

Persian fields:

1. `نام`
2. `ایمیل کاری`
3. `کسب‌وکار و ورک‌فلوی تو`

Persian placeholder:

> مثال: یک مارکت‌پلیس سفر داریم. تیم ما هر روز حدود ۸۰ درخواست تغییر رزرو رو به‌صورت دستی بین ایمیل و CRM پیگیری می‌کنه.

Persian helper:

> آدرس سایت، کسی که الان این کار رو انجام می‌ده، تعداد دفعات تکرار و نتیجه مطلوب رو هم بنویس.

Persian submit:

> Agent Brief من رو درخواست کن

Persian trust text:

> چه با هم کار کنیم چه نه، بریف برای تو می‌مونه. اطلاعاتت فقط برای بررسی ورک‌فلو و جواب‌دادن به خودت استفاده می‌شه.

Persian success title:

> ورک‌فلوت به دستم رسید.

Persian success body:

> چیزی که فرستادی رو بررسی می‌کنم. اگر ورک‌فلو مناسب باشه، برای هماهنگی جلسه با ایمیل بهت خبر می‌دم.

Persian error:

> درخواستت ارسال نشد، اما جواب‌هات هنوز اینجاست. دوباره تلاش کن یا مستقیم ایمیل بزن.

### Data and privacy

- Keep visible fields limited to the three listed above.
- Do not add phone, budget, company size, annual revenue, timeline, or calendar selection.
- Capture source path, locale, referrer, and permitted campaign attribution in hidden fields or submission context.
- Never send names, emails, or workflow descriptions to analytics.
- Keep the general contact form separate.
- Replace the personal email shown in the form only after a branded address has been tested for reliable inbound delivery.

## 9. Live page implementation

### Page purpose

Show credible public proof without forcing a nontechnical buyer to interpret internal runtime language.

### SEO

- Search intent: branded product proof and live AI company demonstration
- Title: `SpielOS Live | See an AI Company Running Itself`
- Description: `See the real goals, departments, approvals, work, and evidence behind the company running on SpielOS.`
- Canonical: `https://spielos.xyz/live/`
- Schema: BreadcrumbList only unless another visible, accurate type is clearly justified
- Required links: Architecture, Services, Agent Brief

### Hero

Label:

> LIVE PROOF

H1:

> This company runs on SpielOS. Here is what it is doing now.

Body:

> SpielOS coordinates our real business goals, Departments, approvals, and results. Start with the plain-language company view. Open the system record when you want the full detail.

Primary CTA:

> Request an Agent Brief

Secondary CTA:

> Understand the architecture

Persian H1:

> این شرکت با SpielOS کار می‌کنه. الان ببین مشغول چه کاریه.

Persian body:

> SpielOS هدف‌های واقعی کسب‌وکار، دپارتمان‌ها، تأییدها و نتیجه‌ها رو هماهنگ می‌کنه. اول نمای ساده شرکت رو ببین. هر وقت جزئیات کامل خواستی، سابقه سیستم رو باز کن.

### Default company view

For each visible active item, show:

1. Plain-language goal title
2. Why it matters to the business
3. Responsible Department
4. Current status in plain English or Persian
5. Latest meaningful result
6. Next action or required human approval
7. Last updated time

Do not show raw goal IDs, stage codes, prerequisite codes, fixture names, batch numbers, or internal file paths in the default view.

### System details

Add a clear `View system details` disclosure. The expanded record may show:

- Canonical goal title
- Stage and run status
- Evidence references
- Decisions
- Technical identifiers
- System-improvement details

Never fabricate friendly labels. Add a separate display-title field to the public live data when a canonical title is not buyer-readable. Keep the raw title available in system details.

### Content grouping

Use two sections:

1. `Business work`
2. `How SpielOS is improving itself`

Business work appears first. System improvements are collapsed by default.

If no result exists, show:

> Still being measured.

Do not imply success from an active or completed technical run.

### Final CTA

H2:

> Start with one workflow from your own company.

Body:

> Describe the repeated work, the current cost, and the result your team needs. I will review whether it is a good first system for SpielOS.

CTA:

> Request an Agent Brief

## 10. Mobile navigation and shared UI

Fix the mobile navigation before the content migration is considered complete.

Current defect: the open menu renders links and the primary CTA over the homepage hero without a clear menu surface.

Required behavior:

- Open menu has an opaque semantic surface and clear separation from page content.
- It does not overlap or visually merge with the hero.
- Page scroll is locked while a full-screen menu is open.
- Focus enters the menu and returns to the trigger after close.
- Escape closes the menu.
- The current route is announced visually and accessibly.
- All text comes from translations.
- Verify at 320, 390, 768, and 1280 pixel widths.
- Verify one dark theme, one light theme, and one monochrome theme.
- Respect reduced motion.
- Use only semantic tokens and Boxicons.

Do not redesign the site. Fix the shared navigation owner and preserve the established visual system.

## 11. SEO migration plan

### Search intent map

| Page | Reader intent | Topic |
|---|---|---|
| Homepage | Understand SpielOS and whether it is relevant | AI workflow systems for established businesses |
| Services | Hire implementation help | AI agent implementation services |
| Agent Brief | Understand and request the first assessment | AI workflow assessment and Agent Brief |
| Architecture | Understand the product mechanism | AI company operating system architecture |
| Live | Verify product and company claims | Live AI company proof |
| Notes | Learn how to reduce repetitive operational work | Specific operator problems and decisions |

Do not create additional SEO landing pages until real search demand, product support, unique intent, and an internal-link path are documented.

### Metadata and localization

- Every English and Persian page has a unique title and description.
- Persian metadata is written as Persian copy, not translated mechanically.
- Each locale self-canonicalizes.
- Emit reciprocal EN and FA hreflang only when both complete equivalents exist.
- Include the new Architecture routes in the sitemap only after both are complete and indexable.
- Remove redirects, noindex pages, and legacy feature URLs from the sitemap.
- All OG copy matches the page language.
- Create a page-specific Architecture OG image using the current brand system.
- Decorative diagrams use empty alt text. Informative diagrams get concise localized alt text.

### On-page rules

- One H1 per page.
- No skipped heading levels.
- Every section heading states one idea.
- Link text describes the destination.
- Do not use `Learn more` as the only link label.
- Do not repeat the Services headline on every page.
- The first paragraph must identify the page's purpose without requiring prior knowledge.
- Architecture terminology must be defined where it first appears.

### Structured data

- Reuse stable shared entity IDs from the SEO skill.
- Do not invent reviews, ratings, pricing, customers, or performance numbers.
- Page schemas must match visible content.
- Breadcrumb URLs must be localized.
- Validate every JSON-LD reference and URL.

### Redirect rules

- Add only direct, evidence-based redirects.
- `/features/` may redirect directly to `/architecture/` once migration is complete.
- Do not create a chain through another legacy route.
- `/waitlist/` and `/fa/waitlist/` redirect directly to their localized Architecture routes per the Waitlist replacement decision; they stay out of the sitemap.
- Do not point internal links at `/features/` after the migration.
- Record each retired feature URL, its evidence, and its final decision in a small migration table before implementation.

### SEO verification

Run after the route and copy changes:

```bash
npm run typecheck
npm run lint
npm run build
npm run seo:check
npm test
```

Also verify:

- Built sitemap parses and contains only canonical indexable URLs.
- No broken internal links.
- No orphan indexable pages.
- No internal links to redirects.
- No duplicate English or Persian titles or descriptions.
- Reciprocal hreflang for every complete locale pair.
- Canonicals return 200.
- Redirects are single-hop 301 responses.
- No localhost, preview, or old-domain URLs appear in built metadata.

Do not claim an SEO improvement from code checks alone. After deployment, compare Search Console impressions, indexed pages, non-branded queries, click-through rate, and conversions by landing page.

## 12. Content Department alignment

Website implementation and Content Department changes are separate workstreams.

Do not modify company runtime or Department behavior as part of a website coding task. Any Department or runtime change requires a separate bounded system-improvement goal, allowed-file scope, tests, and evidence according to `AGENTS.md`.

### Content strategy

Every new public piece must help the canonical buyer with one of four jobs:

1. Recognize a costly repetitive workflow.
2. Understand what makes an AI workflow safe and useful.
3. Evaluate whether a workflow is a good first implementation.
4. See credible evidence from SpielOS operating its own company.

### Content mix

- 40 percent: recognizable operator problems and workflow economics
- 25 percent: implementation lessons, controls, testing, and evidence
- 20 percent: real company proof from SpielOS, translated into buyer meaning
- 15 percent: founder experience and product decisions relevant to the buyer

These are planning ratios, not a publishing quota.

### Content brief gate

Before drafting, require only:

- Reader
- Customer moment
- One idea
- Desired result
- Optional proof
- Search intent when relevant
- Natural next step

Do not make the Agent Brief or the content brief more complex.

### Homepage note selection

A note may appear on the homepage only when all answers are yes:

- Does the title make sense to a nontechnical operator?
- Does it address real work, cost, speed, capacity, quality, or control?
- Does it remain accurate for the current SpielOS product?
- Does it lead naturally to Services, Architecture, Live, or another useful note?

Remove obsolete builder-oriented notes from homepage promotion. Do not delete them automatically. Audit their traffic and backlinks first, then update, archive, noindex, or retain them based on evidence.

### Initial note topics

Use these as briefs, not mandatory titles:

1. How to choose the first workflow to automate with AI
2. What an Agent Brief should define before implementation begins
3. Why a working AI demo can still fail in daily operations
4. Where human approval belongs in an AI workflow
5. How to compare an AI workflow with the way your team works today
6. What SpielOS learned from running real outbound work through its own system

Do not publish all six at once. Start with the highest-intent gap supported by real evidence.

## 13. Implementation sequence

Do not attempt the entire migration in one unreviewed change.

### Phase 0: Preserve and baseline

1. Record current routes, metadata, sitemap, redirects, and conversion events.
2. Capture desktop and mobile screenshots of Homepage, Services, Agent Brief, Features, Live, and the form.
3. Record current click depth and form events.
4. Confirm the waitlist files remain untouched at this phase (Phase 0 precedes the Waitlist replacement decision, which later approves direct redirect wrappers for `src/pages/waitlist.astro` and `src/pages/fa/waitlist.astro`).

Exit condition: baseline evidence exists and current tests pass or existing failures are documented.

### Phase 1: Conversion foundation

1. Standardize `Agent Brief` naming.
2. Create the shared Agent Brief form component.
3. Add the inline form at `/services/agent-brief/#request`.
4. Make primary CTAs direct, crawlable links to that form.
5. Fix modal focus, error preservation, localization, and mobile header spacing.
6. Fix the mobile navigation overlay.

Exit condition: every core route reaches the form in one click and the form works without JavaScript.

### Phase 2: Architecture and Live

1. Create `/architecture/` and `/fa/architecture/`.
2. Build new components outside the protected showcase folder.
3. Use the exact product loop and seven-part company map.
4. Rewrite `/live/` with plain-language default view and expandable system details.
5. Add contextual links among Architecture, Live, Services, and Agent Brief.

Exit condition: a nontechnical operator can explain what SpielOS does, why it is different, and where to start after reading Architecture and Live.

### Phase 3: Homepage and Services

1. Apply the fixed section order and copy.
2. Preserve verified founder evidence in one concise section.
3. Remove obsolete product-builder copy from prominent surfaces.
4. Replace industry-card filler with workflow-based fit examples.
5. Feature only buyer-relevant notes.

Exit condition: Homepage and Services have distinct jobs and tell one coherent story.

### Phase 4: SEO migration

1. Apply unique metadata and localized equivalents.
2. Add Architecture to navigation, footer, sitemap, hreflang, and breadcrumbs.
3. Validate structured data.
4. Redirect `/features/` only after `/architecture/` is complete.
5. Classify feature subpages using search and backlink evidence.
6. Remove all internal links to redirected routes.

Exit condition: build and SEO checks pass with no broken links, duplicate metadata, redirect chains, or invalid locale clusters.

### Phase 5: Content Department handoff

1. Open a separate system-improvement goal.
2. Align Department output with the four content jobs and brief gate in this plan.
3. Preserve the existing simple brief.
4. Add tests that reject builder-first topics, generic AI copy, unsupported claims, and internal runtime language in buyer content.
5. Produce one evidence-backed English and Persian note as a controlled test.

Exit condition: the controlled test passes editorial, translation, ICP, and grounding checks before publishing.

## 14. File ownership guide

The implementer must inspect actual callers before editing. Prefer shared owners over page-local duplication.

Likely files:

- `src/config.ts`: navigation, footer, canonical CTA path
- `src/i18n/translations.ts`: every user-facing EN and FA string
- `src/pages/index.astro`: Homepage composition
- `src/pages/services.astro`: Services composition
- `src/pages/services/agent-brief.astro`: Agent Brief page and inline form
- `src/pages/architecture.astro`: new English Architecture page
- `src/pages/fa/architecture.astro`: thin Persian wrapper
- `src/pages/live.astro`: plain-language Live view
- `src/components/ContactModal.astro`: modal shell only after form extraction
- `src/components/AgentBriefForm.astro`: new shared form owner
- `src/components/Header.astro` or the actual shared navigation owner: mobile navigation fix
- `src/components/architecture/*`: new architecture visuals
- `src/layouts/BaseLayout.astro`: only shared metadata or behavior that truly belongs globally
- `src/pages/features/index.astro`: direct redirect only after migration approval and verification
- sitemap and redirect configuration: update through the repository's current owners
- `docs/site-architecture.md`: update route roles after implementation
- `AGENTS.md`: update the route table and navigation contract after implementation

Do not edit showcase components. The two waitlist page wrappers may contain only the approved direct redirects. Do not add hardcoded English to Astro components. Do not add a second translation store, a second form, or page-local navigation behavior.

## 15. Analytics requirements

Preserve the existing generic lead event vocabulary and follow `.agents/skills/analytics/SKILL.md` if event implementation changes.

At minimum measure:

- Primary CTA click with source page and CTA location
- Agent Brief form view or modal open
- Form start
- Form submit attempt
- Form success
- Form error
- Architecture to Live click
- Architecture to Agent Brief click
- Live system-details expansion

Never send names, emails, business descriptions, workflow descriptions, or textarea contents to analytics.

Primary business funnel:

> Qualified page visit -> Agent Brief form view -> form start -> successful request -> qualified conversation

Do not use pageviews or modal opens as proof of business success.

## 16. Acceptance criteria

The implementation is complete only when every item below passes.

### Strategy and copy

- Homepage, Services, Architecture, and Live have different, obvious jobs.
- `The Company Is the Product`, the commercial result, and the Agent Brief support one another.
- The Agent Brief remains the first client deliverable.
- No core page reads like a generic AI agency template.
- No builder-first language is prominent.
- No em dash exists in new public copy.
- No banned English filler appears in new public copy.
- Every performance claim is framed honestly and supported or identified as a target.

### Conversion

- The Agent Brief form is visible after one click from every core route and the navigation.
- CTA labels match their destination.
- The form has only three visible fields.
- The form works without JavaScript.
- Failed submission preserves the visitor's answers.
- Success copy explains what happens next.

### Product truth

- Architecture uses only Goal, Department, Workflow, Agent, Skill, Connection, and Artifact as the public company vocabulary.
- The public loop is exactly Goal, Observe, Decide, Act, Evaluate.
- Architecture diagrams show relationships, not a loose feature inventory.
- Live data never fabricates business results.
- Internal technical detail remains available without dominating the default Live view.

### Translation

- Every new route has a complete Persian equivalent before hreflang is enabled.
- Persian reads naturally without the English source.
- Glossary terms are consistent.
- UI labels, placeholders, errors, success states, and aria labels are translated.
- RTL layout and directional icons are verified.

### UI and accessibility

- Mobile navigation no longer overlaps page content.
- Modal focus is trapped and restored correctly.
- Keyboard-only navigation completes the conversion flow.
- Focus, loading, success, and error states are visible in dark, light, and monochrome themes.
- Reduced motion is respected.
- Only Boxicons and semantic design tokens are used.

### SEO

- Every indexable page has unique localized metadata.
- Canonicals, hreflang, sitemap, robots, and structured data are valid.
- No important indexable page is orphaned.
- No internal link targets a redirect.
- No redirect chain exists.
- `/waitlist/` and `/fa/waitlist/` redirect directly to their localized Architecture routes and stay out of the sitemap.
- Feature migrations are evidence-based.
- `npm run typecheck`, `npm run lint`, `npm run build`, `npm run seo:check`, and relevant tests pass.

## 17. Stop conditions for the implementing model

Stop and request review if any of these happens:

- Product truth conflicts with this copy.
- A required business metric would need to be invented.
- A feature URL has meaningful search traffic but no clear migration target.
- The implementation would require editing protected showcase components.
- A branded inbound email is proposed but has not been tested.
- Persian meaning is uncertain or conflicts with the glossary.
- A runtime or Department change is required inside the website task.
- Existing user changes overlap the same files and cannot be preserved safely.

Do not solve uncertainty by adding more pages, more fields, more terminology, or more copy.

## 18. Final handoff report format

The implementing model must report:

1. Routes changed or created
2. Exact shared components changed
3. English and Persian copy status
4. CTA and click-depth result
5. Form behavior and accessibility result
6. Metadata, schema, sitemap, hreflang, and redirect changes
7. Feature URLs retained, redirected, noindexed, or deferred, with evidence
8. Tests and checks run with results
9. Screenshots reviewed at required widths and themes
10. Known issues or deferred work

Do not report the project complete while any acceptance criterion is unverified.
