import type { StorySlide } from './story';

/** Classic chapter backbone, with repeated definitions condensed and a practical harness demonstration added. */
type Beat = {concept:number; chapter:number; title:string; line:string; emphasis:string; faTitle:string; faLine:string; faEmphasis:string; mode?:string};
const beats: Beat[] = [
  {
    "concept": 1,
    "chapter": 0,
    "title": "Start with the business objective.",
    "line": "Use AI to create more value: increase capacity, improve quality and lower the cost of getting work done.",
    "emphasis": "business objective.",
    "faTitle": "از هدف کسب‌وکار شروع کنید.",
    "faLine": "هوش مصنوعی باید ارزش بیشتری بسازد: ظرفیت بالاتر، کیفیت بهتر و هزینهٔ کمتر برای انجام کار.",
    "faEmphasis": "هدف کسب‌وکار"
  },
  {
    "concept": 2,
    "chapter": 0,
    "title": "Ask how work gets done.",
    "line": "Tasks are individual actions. Workflows connect them. Systems make the whole way of working repeatable.",
    "emphasis": "how work gets done.",
    "faTitle": "بپرسید کار چگونه انجام می‌شود.",
    "faLine": "وظیفه یک اقدام مشخص است؛ گردش‌کار وظیفه‌ها را متصل می‌کند؛ سیستم این روش کار را تکرارپذیر می‌سازد.",
    "faEmphasis": "کار چگونه انجام می‌شود."
  },
  {
    "concept": 3,
    "chapter": 0,
    "title": "Choose one valuable workflow.",
    "line": "Start with a recurring business problem, redesign the work and prove the result before expanding.",
    "emphasis": "valuable workflow.",
    "faTitle": "یک گردش‌کار ارزشمند انتخاب کنید.",
    "faLine": "از یک مسئلهٔ تکرارشونده شروع کنید، کار را بازطراحی کنید و پیش از گسترش، نتیجه را اثبات کنید.",
    "faEmphasis": "گردش‌کار ارزشمند"
  },
  {
    "concept": 4,
    "chapter": 1,
    "title": "Goal. Set the target.",
    "line": "Set a measurable target for one workflow, with a baseline, an owner and a review date.",
    "emphasis": "Goal.",
    "faTitle": "هدف؛ مقصد را مشخص کنید.",
    "faLine": "برای یک گردش‌کار، هدفی قابل‌سنجش با خط مبنا، مسئول مشخص و زمان بازبینی تعیین کنیم.",
    "faEmphasis": "هدف؛"
  },
  {
    "concept": 106,
    "chapter": 1,
    "mode": "baseline",
    "title": "The baseline makes the problem visible.",
    "line": "Measure handling time, cost per resolution, quality and escalations on comparable cases; separate waiting time from active work.",
    "emphasis": "problem visible.",
    "faTitle": "خط مبنا، مسئله را آشکار می‌کند.",
    "faLine": "زمان رسیدگی، هزینهٔ هر حل مسئله، کیفیت و ارجاع را روی موارد مشابه بسنجیم؛ زمان انتظار را از کار فعال جدا کنیم.",
    "faEmphasis": "مسئله را آشکار"
  },
  {
    "concept": 108,
    "chapter": 1,
    "mode": "decision",
    "title": "Every change is a decision with evidence.",
    "line": "Record the decision, test a version, review the evidence and choose whether to revise, release or stop.",
    "emphasis": "decision with evidence.",
    "faTitle": "هر تغییر، تصمیمی بر پایهٔ شواهد است.",
    "faLine": "تصمیم را ثبت کنیم، یک نسخه را بیازماییم و بر پایهٔ شواهد، اصلاح، انتشار یا توقف را انتخاب کنیم.",
    "faEmphasis": "بر پایهٔ شواهد"
  },
  {
    "concept": 9,
    "chapter": 1,
    "title": "The management framework.",
    "line": "Goal → Observe → Decide → Act → Evaluate sits above the harness that executes the work.",
    "emphasis": "management framework.",
    "faTitle": "چارچوب مدیریت.",
    "faLine": "هدف ← مشاهده ← تصمیم ← اقدام ← ارزیابی؛ چارچوبی برای هدایت هارنسِ اجرای کار.",
    "faEmphasis": "چارچوب مدیریت."
  },
  {
    "concept": 110,
    "chapter": 2,
    "mode": "ownership",
    "title": "Clear responsibilities turn intent into work.",
    "line": "Management sets priorities; analysis specifies the work; architecture and engineering build it; evaluation checks the evidence.",
    "emphasis": "Clear responsibilities",
    "faTitle": "مسئولیت‌های روشن، تصمیم را به کار تبدیل می‌کنند.",
    "faLine": "مدیریت اولویت می‌دهد؛ تحلیل، کار را تعریف می‌کند؛ معماری و مهندسی آن را می‌سازند؛ ارزیابی، شواهد را بررسی می‌کند.",
    "faEmphasis": "مسئولیت‌های روشن"
  },
  {
    "concept": 111,
    "chapter": 2,
    "mode": "handoff",
    "title": "The work moves through concrete handoffs.",
    "line": "A process specification becomes acceptance tests, a versioned workflow and a release decision; each handoff has an owner.",
    "emphasis": "concrete handoffs.",
    "faTitle": "کار با تحویل خروجی‌های مشخص پیش می‌رود.",
    "faLine": "مشخصات فرایند به آزمون پذیرش، گردش‌کار نسخه‌بندی‌شده و تصمیم انتشار تبدیل می‌شود؛ هر تحویل، مسئول دارد.",
    "faEmphasis": "خروجی‌های مشخص"
  },
  {
    "concept": 15,
    "chapter": 2,
    "title": "One transformation team. Every department.",
    "line": "Business teams own their outcomes. The transformation team helps them continuously improve.",
    "emphasis": "Every department.",
    "faTitle": "یک تیم تحول. برای تمام واحدها.",
    "faLine": "هر واحد مسئول نتایج خود است؛ تیم تحول به بهبود مستمر آن کمک می‌کند.",
    "faEmphasis": "تمام واحدها."
  },
  {
    "concept": 16,
    "chapter": 3,
    "title": "Your business is the context.",
    "line": "AI needs your strategy, policies, knowledge, people and systems to make useful decisions.",
    "emphasis": "the context.",
    "faTitle": "کسب‌وکار شما، زمینهٔ کار است.",
    "faLine": "هوش مصنوعی برای تصمیم مفید به راهبرد، سیاست‌ها، دانش، افراد و سیستم‌های شما نیاز دارد.",
    "faEmphasis": "زمینهٔ کار است."
  },
  {
    "concept": 17,
    "chapter": 3,
    "title": "SpielOS is the shared operating system.",
    "line": "The product brings context, memory, the harness, tools, guardrails and observability into one workspace.",
    "emphasis": "SpielOS",
    "faTitle": "SpielOS سیستم‌عامل مشترک شرکت است.",
    "faLine": "این محصول، زمینه، حافظه، هارنس، ابزارها، کنترل‌ها و مشاهده‌پذیری را در یک محیط کاری جمع می‌کند.",
    "faEmphasis": "SpielOS"
  },
  {
    "concept": 19,
    "chapter": 3,
    "title": "Keep the tools that work.",
    "line": "Connect your preferred models and platforms as execution providers inside one coherent system.",
    "emphasis": "tools that work.",
    "faTitle": "ابزارهای کارآمد را نگه دارید.",
    "faLine": "مدل‌ها و پلتفرم‌های منتخب را به‌عنوان ارائه‌دهندهٔ اجرا به یک سیستم هماهنگ متصل کنید.",
    "faEmphasis": "ابزارهای کارآمد"
  },
  {
    "concept": 51,
    "chapter": 3,
    "title": "The OS becomes a product surface.",
    "line": "Context, execution and evidence meet in one inspectable workspace.",
    "emphasis": "product surface.",
    "faTitle": "سیستم‌عامل به یک محصول ملموس تبدیل می‌شود.",
    "faLine": "زمینه، اجرا و شواهد در یک محیط کاری قابل‌بررسی کنار هم قرار می‌گیرند.",
    "faEmphasis": "محصول ملموس"
  },
  {
    "concept": 20,
    "chapter": 3,
    "title": "Company context. SpielOS. Department systems.",
    "line": "One AI operating system connects your knowledge, harness and execution providers to business outcomes.",
    "emphasis": "SpielOS.",
    "faTitle": "زمینهٔ شرکت. SpielOS. سیستم‌های واحدها.",
    "faLine": "یک سیستم‌عامل هوش مصنوعی، دانش، هارنس و ابزارهای اجرا را به نتایج کسب‌وکار متصل می‌کند.",
    "faEmphasis": "SpielOS."
  },
  {
    "concept": 120,
    "chapter": 4,
    "mode": "prompt",
    "title": "The build begins with an executable brief.",
    "line": "Request a delivery-exception workflow, attach the policy and acceptance tests, and keep deployment disabled until review.",
    "emphasis": "executable brief.",
    "faTitle": "ساخت، با شرح کاری قابل‌اجرا آغاز می‌شود.",
    "faLine": "گردش‌کار رسیدگی به مشکل تحویل را درخواست کنیم، سیاست و آزمون‌های پذیرش را پیوست کنیم و انتشار را تا بازبینی غیرفعال نگه داریم.",
    "faEmphasis": "شرح کاری قابل‌اجرا"
  },
  {
    "concept": 121,
    "chapter": 4,
    "mode": "context",
    "title": "The brief becomes a bounded working context.",
    "line": "Load the process specification, discover available Activepieces pieces and connections, and identify missing permissions before acting.",
    "emphasis": "bounded working context.",
    "faTitle": "شرح کار به زمینهٔ اجرایی با مرزهای روشن تبدیل می‌شود.",
    "faLine": "مشخصات فرایند را بارگذاری کنیم، قطعه‌ها و اتصال‌های موجود Activepieces را بشناسیم و پیش از اقدام، مجوزهای لازم را مشخص کنیم.",
    "faEmphasis": "مرزهای روشن"
  },
  {
    "concept": 122,
    "chapter": 4,
    "mode": "harness",
    "title": "The harness coordinates each step.",
    "line": "Plan → call a tool → inspect the result → continue or recover; context, permissions and completion checks surround the loop.",
    "emphasis": "coordinates each step.",
    "faTitle": "هارنس هر مرحله را هماهنگ می‌کند.",
    "faLine": "برنامه‌ریزی ← فراخوانی ابزار ← بررسی نتیجه ← ادامه یا بازیابی؛ زمینه، مجوزها و بررسی تکمیل کار، این چرخه را احاطه می‌کنند.",
    "faEmphasis": "هر مرحله را هماهنگ می‌کند."
  },
  {
    "concept": 123,
    "chapter": 4,
    "mode": "build",
    "title": "Tool calls turn the plan into a workflow.",
    "line": "Use documented discovery and build tools to create a flow, then inspect its structure; this walkthrough is an illustrative example.",
    "emphasis": "into a workflow.",
    "faTitle": "فراخوانی ابزارها، برنامه را به گردش‌کار تبدیل می‌کند.",
    "faLine": "با ابزارهای مستندِ کشف و ساخت، گردش‌کار ایجاد و ساختار آن را بررسی کنیم؛ این نمایش، یک مثال توضیحی است.",
    "faEmphasis": "به گردش‌کار"
  },
  {
    "concept": 124,
    "chapter": 4,
    "mode": "canvas",
    "title": "The result is an inspectable workflow.",
    "line": "Ticket trigger → order lookup → policy retrieval → draft → routing decision → review or delivery → outcome log.",
    "emphasis": "inspectable workflow.",
    "faTitle": "نتیجه، یک گردش‌کار قابل‌بررسی است.",
    "faLine": "دریافت تیکت ← بررسی سفارش ← بازیابی سیاست ← پیش‌نویس ← تصمیم ارجاع ← بازبینی یا ارسال ← ثبت نتیجه.",
    "faEmphasis": "گردش‌کار قابل‌بررسی"
  },
  {
    "concept": 125,
    "chapter": 4,
    "mode": "evals",
    "title": "Tests check behavior before release.",
    "line": "Validate the flow structure, then test representative cases against explicit expected outcomes; a valid flow is not proof of a good answer.",
    "emphasis": "before release.",
    "faTitle": "آزمون‌ها رفتار را پیش از انتشار بررسی می‌کنند.",
    "faLine": "ساختار گردش‌کار را اعتبارسنجی کنیم؛ سپس موارد نمونه را با نتایج موردانتظار بسنجیم. ساختار معتبر، کیفیت پاسخ را ثابت نمی‌کند.",
    "faEmphasis": "پیش از انتشار"
  },
  {
    "concept": 126,
    "chapter": 4,
    "mode": "repair",
    "title": "A failed case shows what needs to change.",
    "line": "An unknown order must not produce an invented delivery date; repair the branch and rerun the failing case plus regression tests.",
    "emphasis": "what needs to change.",
    "faTitle": "یک مورد شکست‌خورده، تغییر لازم را نشان می‌دهد.",
    "faLine": "سفارش نامشخص نباید تاریخ تحویل ساختگی تولید کند؛ شاخهٔ مربوط را اصلاح و آزمون شکست‌خورده و آزمون‌های بازگشت را تکرار کنیم.",
    "faEmphasis": "تغییر لازم"
  },
  {
    "concept": 127,
    "chapter": 4,
    "mode": "run",
    "title": "The completed workflow handles a customer event.",
    "line": "After approval and controlled release, a new ticket enters the deployed workflow; follow its tools, decision and output separately from the build run.",
    "emphasis": "customer event.",
    "faTitle": "گردش‌کار کامل، به رویداد مشتری رسیدگی می‌کند.",
    "faLine": "پس از تأیید و انتشار کنترل‌شده، تیکت تازه وارد گردش‌کار می‌شود؛ ابزارها، تصمیم و خروجی آن را جدا از اجرای ساخت دنبال کنیم.",
    "faEmphasis": "رویداد مشتری"
  },
  {
    "concept": 28,
    "chapter": 5,
    "title": "Procedural memory knows how.",
    "line": "Procedural memory stores proven methods so the next run can reuse them.",
    "emphasis": "how",
    "faTitle": "حافظهٔ رویه‌ای می‌داند چگونه.",
    "faLine": "حافظهٔ رویه‌ای روش‌های آزموده را نگه می‌دارد تا اجرای بعدی از آن‌ها استفاده کند.",
    "faEmphasis": "چگونه"
  },
  {
    "concept": 31,
    "chapter": 5,
    "title": "Give this task the right knowledge.",
    "line": "Retrieve what matters, leave out what does not and assemble a focused working context.",
    "emphasis": "right knowledge.",
    "faTitle": "دانش مناسب را به این وظیفه برسانید.",
    "faLine": "اطلاعات مرتبط را بازیابی کنید، موارد اضافی را کنار بگذارید و زمینه‌ای متمرکز بسازید.",
    "faEmphasis": "دانش مناسب"
  },
  {
    "concept": 33,
    "chapter": 5,
    "title": "The next run starts better informed.",
    "line": "Methods, facts and experience feed the work; the result adds another useful lesson.",
    "emphasis": "better informed.",
    "faTitle": "اجرای بعدی با آگاهی بیشتر شروع می‌شود.",
    "faLine": "روش‌ها، واقعیت‌ها و تجربه، ورودی کار هستند؛ نتیجه نیز آموخته‌ای تازه اضافه می‌کند.",
    "faEmphasis": "آگاهی بیشتر"
  },
  {
    "concept": 112,
    "chapter": 6,
    "mode": "process",
    "title": "The current process reveals the bottleneck.",
    "line": "Find the trigger, information sources, decisions, handoffs and failure paths in today’s delivery-exception process.",
    "emphasis": "reveals the bottleneck.",
    "faTitle": "فرایند فعلی، گلوگاه را نشان می‌دهد.",
    "faLine": "محرک، منابع اطلاعات، تصمیم‌ها، تحویل‌ها و مسیرهای شکستِ فرایند فعلی رسیدگی به مشکل تحویل را پیدا کنیم.",
    "faEmphasis": "گلوگاه"
  },
  {
    "concept": 115,
    "chapter": 6,
    "mode": "acceptance",
    "title": "Acceptance criteria define the redesigned work.",
    "line": "Specify grounded answers, correct routing, duplicate handling and safe behavior when order data or policy is missing.",
    "emphasis": "redesigned work.",
    "faTitle": "معیارهای پذیرش، کارِ بازطراحی‌شده را تعریف می‌کنند.",
    "faLine": "پاسخ مستند، ارجاع درست، مدیریت موارد تکراری و رفتار ایمن هنگام نبود اطلاعات سفارش یا سیاست را تعریف کنیم.",
    "faEmphasis": "کارِ بازطراحی‌شده"
  },
  {
    "concept": 39,
    "chapter": 6,
    "title": "From manual handoffs to measured results.",
    "line": "A customer support request becomes a connected workflow with checks, escalation and feedback.",
    "emphasis": "measured results.",
    "faTitle": "از تحویل دستی کار تا نتایج قابل‌سنجش.",
    "faLine": "درخواست پشتیبانی به گردش‌کاری متصل، همراه با کنترل، ارجاع و بازخورد تبدیل می‌شود.",
    "faEmphasis": "نتایج قابل‌سنجش."
  },
  {
    "concept": 40,
    "chapter": 7,
    "title": "One win becomes a team capability.",
    "line": "Combine proven workflows to change how a department handles an entire class of work.",
    "emphasis": "team capability.",
    "faTitle": "یک موفقیت، به توانمندی تیم تبدیل می‌شود.",
    "faLine": "گردش‌کارهای آزموده را ترکیب کنید تا روش انجام یک دسته از کارهای واحد تغییر کند.",
    "faEmphasis": "توانمندی تیم"
  },
  {
    "concept": 41,
    "chapter": 7,
    "title": "Share the foundation. Adapt the work.",
    "line": "Departments use common infrastructure while keeping their own context, workflows and success measures.",
    "emphasis": "Adapt the work.",
    "faTitle": "زیرساخت مشترک؛ کار متناسب با هر واحد.",
    "faLine": "واحدها زیرساخت مشترک دارند، اما زمینه، گردش‌کارها و معیارهای موفقیت خود را حفظ می‌کنند.",
    "faEmphasis": "کار متناسب با هر واحد."
  },
  {
    "concept": 43,
    "chapter": 7,
    "title": "Specialized teams. Shared intelligence.",
    "line": "Each department moves toward its own outcomes on one company-wide foundation.",
    "emphasis": "Shared intelligence.",
    "faTitle": "تیم‌های تخصصی. هوشمندی مشترک.",
    "faLine": "هر واحد روی یک زیرساخت سراسری، به سمت نتایج خود حرکت می‌کند.",
    "faEmphasis": "هوشمندی مشترک."
  },
  {
    "concept": 128,
    "chapter": 8,
    "mode": "tracing",
    "title": "The trace explains what happened.",
    "line": "Inspect the order lookup, retrieved evidence, model call, routing decision, latency and cost—not just the final answer.",
    "emphasis": "what happened.",
    "faTitle": "ردیابی نشان می‌دهد چه اتفاقی افتاده است.",
    "faLine": "بررسی سفارش، شواهد بازیابی‌شده، فراخوانی مدل، تصمیم ارجاع، تأخیر و هزینه را ببینیم؛ نه فقط پاسخ نهایی را.",
    "faEmphasis": "چه اتفاقی افتاده است."
  },
  {
    "concept": 129,
    "chapter": 8,
    "mode": "adoption",
    "title": "Evals ask whether it was good.",
    "line": "Compare versions on the same cases, inspect failures and track groundedness, routing accuracy and policy compliance.",
    "emphasis": "whether it was good.",
    "faTitle": "ارزیابی می‌پرسد نتیجه چقدر خوب بوده است.",
    "faLine": "نسخه‌ها را روی موارد یکسان مقایسه کنیم، شکست‌ها را ببینیم و استنادپذیری، دقت ارجاع و رعایت سیاست را بسنجیم.",
    "faEmphasis": "چقدر خوب"
  },
  {
    "concept": 130,
    "chapter": 8,
    "mode": "scorecard",
    "title": "The business scorecard asks: did it matter?",
    "line": "Compare the pilot with its baseline on comparable work; report quality, time, cost, escalations and adoption together.",
    "emphasis": "did it matter?",
    "faTitle": "سنجه‌های کسب‌وکار می‌پرسند: چه ارزشی ایجاد شد؟",
    "faLine": "پایلوت را روی کارهای مشابه با خط مبنا مقایسه کنیم؛ کیفیت، زمان، هزینه، ارجاع و میزان استفاده را کنار هم گزارش دهیم.",
    "faEmphasis": "چه ارزشی ایجاد شد؟"
  },
  {
    "concept": 48,
    "chapter": 8,
    "title": "Trace → Evaluate → Learn → Improve.",
    "line": "Observability feeds Observe; Evals and business outcomes feed Evaluate.",
    "emphasis": "Improve.",
    "faTitle": "ردیابی ← ارزیابی ← یادگیری ← بهبود.",
    "faLine": "مشاهده‌پذیری به «مشاهده» و ارزیابی‌های کیفیت و نتایج کسب‌وکار به «ارزیابی» ورودی می‌دهند.",
    "faEmphasis": "بهبود."
  },
  {
    "concept": 49,
    "chapter": 9,
    "title": "Build the ability to keep improving.",
    "line": "An AI-first company can continuously redesign its work while retaining control, knowledge and accountability.",
    "emphasis": "keep improving.",
    "faTitle": "توانایی بهبود مستمر را بسازید.",
    "faLine": "شرکت هوش‌مصنوعی‌محور، با حفظ کنترل، دانش و مسئولیت‌پذیری، کار خود را پیوسته بازطراحی می‌کند.",
    "faEmphasis": "بهبود مستمر"
  },
  {
    "concept": 135,
    "chapter": 9,
    "mode": "pilot",
    "title": "The next decision is a bounded pilot.",
    "line": "Choose the workflow, confirm its owner and baseline, agree on resources and acceptance criteria, then schedule an evidence-based review.",
    "emphasis": "bounded pilot.",
    "faTitle": "تصمیم بعدی، یک پایلوت با محدودهٔ روشن است.",
    "faLine": "گردش‌کار را انتخاب کنیم، مسئول و خط مبنا را تأیید کنیم، منابع و معیارهای پذیرش را توافق کنیم و موعد بازبینی شواهد را تعیین کنیم.",
    "faEmphasis": "پایلوت با محدودهٔ روشن"
  },
  {
    "concept": 134,
    "chapter": 9,
    "mode": "whole-system",
    "title": "The whole transformation, connected.",
    "line": "Goals guide management; the team redesigns work; SpielOS supports execution; evidence informs the next decision.",
    "emphasis": "connected.",
    "faTitle": "تمام مسیر تحول، به‌هم‌پیوسته.",
    "faLine": "هدف‌ها مدیریت را هدایت می‌کنند؛ تیم، کار را بازطراحی می‌کند؛ SpielOS از اجرا پشتیبانی می‌کند؛ شواهد، تصمیم بعدی را شکل می‌دهند.",
    "faEmphasis": "به‌هم‌پیوسته."
  },
  {
    "concept": 50,
    "chapter": 9,
    "title": "Thank you for your time.",
    "line": "One workflow. Measured evidence. A repeatable way to improve.",
    "emphasis": "Thank you",
    "faTitle": "از وقتی که گذاشتید سپاسگزاریم.",
    "faLine": "یک گردش‌کار؛ شواهد قابل‌سنجش؛ روشی تکرارپذیر برای بهبود.",
    "faEmphasis": "سپاسگزاریم."
  }
];
type ChapterOpening = [string,string,string,string,string,string];
const openings: Record<number,ChapterOpening> = {
  "0": [
    "AI transformation.",
    "Start with the business objective, then understand how work gets done.",
    "transformation.",
    "تحول با هوش مصنوعی.",
    "از هدف کسب‌وکار شروع کنید؛ سپس ببینید کار چگونه انجام می‌شود.",
    "تحول"
  ],
  "1": [
    "The management framework.",
    "Goal → Observe → Decide → Act → Evaluate.",
    "framework.",
    "چارچوب مدیریت.",
    "هدف ← مشاهده ← تصمیم ← اقدام ← ارزیابی.",
    "مدیریت."
  ],
  "2": [
    "The transformation team.",
    "The people who design, build and improve the company’s AI systems.",
    "team.",
    "تیم تحول.",
    "افرادی که سیستم‌های هوش مصنوعی شرکت را طراحی می‌کنند، می‌سازند و بهبود می‌دهند.",
    "تحول."
  ],
  "3": [
    "SpielOS. The company OS.",
    "Your company context, harness, memory and tools in one operating system.",
    "company OS.",
    "SpielOS؛ سیستم‌عامل شرکت.",
    "زمینهٔ شرکت، هارنس، حافظه و ابزارها در یک سیستم‌عامل مشترک.",
    "سیستم‌عامل شرکت."
  ],
  "4": [
    "Inside the AI harness.",
    "Follow one workflow from a Codex brief through tools, testing and a controlled run.",
    "AI harness.",
    "درون هارنس هوش مصنوعی.",
    "یک گردش‌کار را از شرح کار در Codex تا فراخوانی ابزار، آزمون و اجرای کنترل‌شده دنبال کنیم.",
    "هارنس هوش مصنوعی."
  ],
  "5": [
    "A company that remembers.",
    "Keep the knowledge, methods and lessons that make the next run better.",
    "remembers.",
    "شرکتی که به یاد می‌سپارد.",
    "دانش، روش‌ها و آموخته‌هایی را نگه دارید که اجرای بعدی را بهتر می‌کنند.",
    "به یاد می‌سپارد."
  ],
  "6": [
    "Redesign the work.",
    "Start with the business process. Choose the technology after.",
    "work.",
    "بازطراحیِ کار.",
    "از فرایند کسب‌وکار شروع کنید؛ فناوری را بعد از آن انتخاب کنید.",
    "کار."
  ],
  "7": [
    "Prove it. Then scale it.",
    "Turn individual wins into a capability the whole company can use.",
    "scale it.",
    "اثبات کنید؛ سپس گسترش دهید.",
    "موفقیت‌های تک‌موردی را به قابلیتی تبدیل کنید که تمام شرکت از آن استفاده کند.",
    "گسترش دهید."
  ],
  "8": [
    "Observability & Evals.",
    "Trace every run. Evaluate its quality. Measure its business impact.",
    "Evals.",
    "مشاهده‌پذیری و ارزیابی‌ها.",
    "هر اجرا را ردیابی کنید؛ کیفیت آن و اثرش بر کسب‌وکار را بسنجید.",
    "ارزیابی‌ها."
  ],
  "9": [
    "The AI-first organization.",
    "A company with the ability to keep improving how work happens.",
    "AI-first organization.",
    "سازمانی با محوریت هوش مصنوعی.",
    "شرکتی که می‌تواند شیوهٔ انجام کار را پیوسته بهتر کند.",
    "با محوریت هوش مصنوعی."
  ]
};

const assembled = new Set([3,9,15,20,124,127,33,39,43,48,134,50]);
export const storySlides: StorySlide[] = beats.flatMap((beat,index) => {
  const slide={id:0,concept:beat.concept,chapter:beat.chapter,title:beat.title,line:beat.line,assembly:assembled.has(beat.concept),intro:false};
  if(index===0||beats[index-1].chapter!==beat.chapter){
    const intro=openings[beat.chapter];
    return [{...slide,concept:0,title:intro[0],line:intro[1],assembly:false,intro:true},slide];
  }
  return [slide];
}).map((slide,index)=>({...slide,id:index+1}));
export const compactDetails: Record<number,{mode:string}> = Object.fromEntries(beats.filter(b=>b.mode).map(b=>[b.concept,{mode:b.mode!}]));
export const compactTranslations: Record<string,string> = Object.fromEntries([
  ...beats.flatMap(b=>[[b.title,b.faTitle],[b.line,b.faLine],[b.emphasis,b.faEmphasis]]),
  ...Object.values(openings).flatMap(b=>[[b[0],b[3]],[b[1],b[4]],[b[2],b[5]]]),
]);
export const emphases: Record<number,string> = Object.fromEntries(beats.map(b=>[b.concept,b.emphasis]));
export const titleOverrides: Record<number,string> = {};
export const compactCopy = beats;
export const chapterOpenings: [string,string,string][] = Array.from({length:10},(_,chapter)=>{
  const opening=openings[chapter];return [opening[0],opening[1],opening[2]];
});
export const compactChapterOrder = [0,1,2,3,4,5,6,7,8,9];
