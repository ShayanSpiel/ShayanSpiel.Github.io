#!/usr/bin/env python3
"""
SpielOS Outbound — templates and signatures.

Templates are keyed by language ("English" or "Persian"); each language has
VARIANT_ROTATE-based A/B variants. Use {placeholders} for personalization.

Available placeholders:
  {contact_name}, {first_name}, {company}, {title}, {domain},
  {personalization_hook}, {suggested_cta}, {website}, {country}, {segment},
  {SIGNATURE_HTML}, {SIGNATURE_TEXT}
"""

from config import (
    FROM_NAME,
    SIGNATURE_TITLE,
    SIGNATURE_AVATAR_URL,
    SIGNATURE_LINKEDIN,
    SIGNATURE_X,
    SIGNATURE_SERVICES,
)

SIGNATURE_HTML = f"""\
<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:24px;border-top:1px solid #e5e5e5;padding-top:16px;font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.5;color:#333333;">
  <tr>
    <td style="padding-right:12px;vertical-align:middle;">
      <img src="{SIGNATURE_AVATAR_URL}" alt="{FROM_NAME}" width="48" height="48" style="border-radius:50%;display:block;" />
    </td>
    <td style="vertical-align:middle;">
      <div style="font-size:14px;font-weight:bold;color:#111111;">{FROM_NAME}</div>
      <div style="color:#555555;">{SIGNATURE_TITLE}</div>
      <div style="margin-top:4px;">
        <a href="{SIGNATURE_LINKEDIN}" style="color:#0a66c2;text-decoration:none;">LinkedIn</a>
        &nbsp;&middot;&nbsp;
        <a href="{SIGNATURE_X}" style="color:#111111;text-decoration:none;">X</a>
        &nbsp;&middot;&nbsp;
        <a href="{SIGNATURE_SERVICES}" style="color:#333333;text-decoration:none;">spielos.xyz/services</a>
      </div>
    </td>
  </tr>
</table>"""

SIGNATURE_TEXT = f"""\
{FROM_NAME}
{SIGNATURE_TITLE}
LinkedIn: {SIGNATURE_LINKEDIN}
X: {SIGNATURE_X}
{SIGNATURE_SERVICES}"""

TEMPLATES = {
    "English": [
        {
            "label": "scarcity-handpicked",
            "subject": "I picked {company} for a free brief",
            "body_html": """\
<p>Hi {first_name},</p>
<p>This week I'm giving away 3 free pilot briefs, and I hand-picked {company} for one.</p>
<p>As {title} in a {segment} business, you see it daily: the sourcing, follow-ups, and handoffs between tools eat hours that should go into revenue.</p>
<p>Each pilot is a one-page <a href="https://spielos.xyz/services/agent-brief/" style="color:#111111;">Agent Brief</a>: one workflow mapped end to end, what automation would look like, and the expected ROI. You keep it whether or not we ever work together.</p>
<p>If you want the brief, reply "map" and I'll handle the rest.</p>
<p>Best,<br>Shayan</p>
{SIGNATURE_HTML}""",
            "body_text": """\
Hi {first_name},

This week I'm giving away 3 free pilot briefs, and I hand-picked {company} for one.

As {title} in a {segment} business, you see it daily: the sourcing, follow-ups, and handoffs between tools eat hours that should go into revenue.

Each brief is a one-page Agent Brief: one workflow mapped end to end, what automation would look like, and the expected ROI. You keep it either way.

See the brief format: https://spielos.xyz/services/agent-brief/

If you want it, reply "map" and I'll handle the rest.

Best,
Shayan

{SIGNATURE_TEXT}""",
        },
        {
            "label": "curiosity-gap",
            "subject": "A question about a day at {company}",
            "body_html": """\
<p>Hi {first_name},</p>
<p>What's the one workflow at {company} you'd hand off if you could? For most {segment} businesses it's the repetitive work between tools: sourcing, follow-ups, reporting.</p>
<p>This week I'm giving 3 free pilot briefs, and I'd like {company} to be one of them. Each brief is a one-page <a href="https://spielos.xyz/services/agent-brief/" style="color:#111111;">Agent Brief</a>: the workflow mapped today, the automated version, and the measurable result. No strings, you keep it either way.</p>
<p>Reply "map" and I'll send the details.</p>
<p>Best,<br>Shayan</p>
{SIGNATURE_HTML}""",
            "body_text": """\
Hi {first_name},

What's the one workflow at {company} you'd hand off if you could? For most {segment} businesses it's the sourcing or follow-up between tools.

This week I'm giving 3 free pilot briefs, and I'd like {company} to be one of them. Each brief is a one-page Agent Brief: the workflow mapped today, the automated version, and the result. No strings attached.

See the brief format: https://spielos.xyz/services/agent-brief/

Reply "map" and I'll send the details.

Best,
Shayan

{SIGNATURE_TEXT}""",
        },
        {
            "label": "pilot-window",
            "subject": "3 slots this week, {company} gets one",
            "body_html": """\
<p>Hi {first_name},</p>
<p>This week I'm doing 3 free pilot briefs, and I kept a slot for {company}.</p>
<p>One brief is one page: <a href="https://spielos.xyz/services/agent-brief/" style="color:#111111;">an Agent Brief</a> that maps one repetitive workflow, what automation looks like, and the ROI you could expect. Yours to keep regardless.</p>
<p>Reply "map" and I'll hold the slot for {company}.</p>
<p>Best,<br>Shayan</p>
{SIGNATURE_HTML}""",
            "body_text": """\
Hi {first_name},

This week I'm doing 3 free pilot briefs, and I kept a slot for {company}.

One brief is one page: the workflow mapped, the automation shape, and the expected ROI. Yours to keep regardless.

See the brief format: https://spielos.xyz/services/agent-brief/

Reply "map" and I'll hold the slot.

Best,
Shayan

{SIGNATURE_TEXT}""",
        },
    ],
    "Persian": [
        {
            "label": "scarcity-handpicked",
            "subject": "یک بریف رایگان برای {company} رزرو کردم",
            "body_html": """\
<p>سلام {first_name}،</p>
<p>این هفته ۳ بریف آزمایشی رایگان می‌دهم، و {company} را برای یکی از آن‌ها انتخاب کرده‌ام.</p>
<p>به‌عنوان {title} در کسب‌وکار {segment}، هر روز می‌بینید: کارهای تکراری بین ابزارها ساعت‌های زیادی را می‌گیرد که باید صرف درآمد شود.</p>
<p>هر بریف یک <a href="https://spielos.xyz/services/agent-brief/" style="color:#2f81f7;">Agent Brief</a> یک‌صفحه‌ای است: نقشه کامل یک ورک‌فلو، شکل اتوماسیون و ROI مورد انتظار. چه با هم کار کنیم چه نه، بریف مال شماست.</p>
<p>اگر می‌خواهید، کافی است «map» را پاسخ بدهید.</p>
<p>با احترام،<br>شایان</p>
{SIGNATURE_HTML}""",
            "body_text": """\
سلام {first_name}،

این هفته ۳ بریف آزمایشی رایگان می‌دهم، و {company} را برای یکی از آن‌ها انتخاب کرده‌ام.

به‌عنوان {title} در کسب‌وکار {segment}، هر روز می‌بینید: کارهای تکراری بین ابزارها ساعت‌ها می‌برد.

هر بریف یک Agent Brief یک‌صفحه‌ای است: نقشه کامل یک ورک‌فلو، شکل اتوماسیون و ROI. چه با هم کار کنیم چه نکنیم، بریف مال شماست.

قالب بریف: https://spielos.xyz/services/agent-brief/

اگر خواستید، «map» پاسخ دهید.

با احترام،
شایان

{SIGNATURE_TEXT}""",
        },
        {
            "label": "curiosity-gap",
            "subject": "سوالی از یک روز کاری در {company}",
            "body_html": """\
<p>سلام {first_name}،</p>
<p>این هفته ۳ بریف آزمایشی رایگان می‌دهم و {company} را برای یکی از آن‌ها انتخاب کرده‌ام.</p>
<p>به‌عنوان {title} در کسب‌وکار {segment}، اگر می‌خواستید یک ورک‌فلو را به ابزارها بسپارید، کدام بود؟ معمولاً کارهای تکراری بین ابزارها: جستجو، پیگیری، گزارش‌ها.</p>
<p>یک بریف یک‌صفحه‌ای است: <a href="https://spielos.xyz/services/agent-brief/" style="color:#2f81f7;">قالب Agent Brief</a> برای همان ورک‌فلو، بدون هیچ تعهدی. اگر خواستید، «map» را بگویید.</p>
<p>با احترام،<br>شایان</p>
{SIGNATURE_HTML}""",
            "body_text": """\
سلام {first_name}،

این هفته ۳ بریف آزمایشی رایگان می‌دهم و {company} را انتخاب کرده‌ام.

به‌عنوان {title} در کسب‌وکار {segment}، اگر می‌خواستید یک ورک‌فلو را بسپارید، کدام بود؟ معمولاً: کارهای تکراری بین ابزارها.

یک بریف یک‌صفحه‌ای بدون هیچ تعهدی. اگر خواستید «map» بگویید.

{SIGNATURE_TEXT}""",
        },
        {
            "label": "pilot-window",
            "subject": "این هفته ۳ اسلات؛ یکی برای {company}",
            "body_html": """\
<p>سلام {first_name}،</p>
<p>این هفته ۳ بریف آزمایشی رایگان می‌دهم و یک اسلات را برای {company} نگه داشته‌ام.</p>
<p>به‌عنوان {title}، ترجیح می‌دهم کار را نشان بدهم تا درباره‌اش حرف بزنم.</p>
<p>هر بریف یک صفحه است: <a href="https://spielos.xyz/services/agent-brief/" style="color:#2f81f7;">قالب Agent Brief</a> برای یک ورک‌فلو. نتیجه کامل مال شماست.</p>
<p>اگر خواستید، «map» بگویید تا اسلات را قطعی کنم.</p>
<p>با احترام،<br>شایان</p>
{SIGNATURE_HTML}""",
            "body_text": """سلام {first_name}،

این هفته ۳ بریف آزمایشی رایگان می‌دهم و یک اسلات را برای {company} نگه داشته‌ام.

اگر خواستید، «map» بگویید.

با احترام،
شایان

{SIGNATURE_TEXT}""",
        },
    ],
}
