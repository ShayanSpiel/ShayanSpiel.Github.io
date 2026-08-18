"""Content Department eval suites — grounded quality standards for campaign copy.

`content-copy-top10` is the judge-enforced content/ICP standard: ten criteria
grounded in the canonical strategy files and skills, judged PER ITEM against
the item's brief AND both platform renditions (threads + youtube copy).  The
content-campaign quality_gate requires a passing eval_report for this suite
before a campaign can advance to campaign_ready.

Adding a suite to ANY department follows the same Lego contract:
1. create `departments/<name>/evals.py` exporting EVAL_SUITES
2. register criteria with source-file grounding (strategy/skill paths)
3. declare `eval_suites = (...)` on the Department class
4. require a passing eval_report evidence in the machine step that gates
"""

from ...evals.models import EvalCriterion, EvalSuite

ICPC = ".agents/company/strategy/icp.md"
VOICE = ".agents/company/strategy/voice.md"
CONTENT_README = ".agents/company/departments/content/README.md"
COPYWRITING_EN = ".agents/skills/copywriting-en/SKILL.md"

CONTENT_COPY_TOP10 = EvalSuite(
    id="content-copy-top10",
    name="Content copy vs the ICP quality standard (top 10)",
    scope="content-copy",
    department_id="content",
    payload_kind="campaign_manifest",
    description=(
        "Ten ICP-grounded criteria judged per item against the item brief and "
        "both platform renditions. Every criterion must pass (all_pass, "
        "min_score 1.0) before campaign copy can advance through the quality gate."
    ),
    validity="business",
    thresholds={"all_pass": True, "min_score": 1.0},
    payload_id_selector=lambda payload: str(payload.get("batch_id") or payload.get("id") or "payload"),
    item_selector=lambda payload: [
        (item["item_id"], item) for item in (payload.get("items") or [])
    ],
    criteria=(
        EvalCriterion(
            id="one_reader",
            name="One ICP reader",
            description=(
                "The piece addresses exactly one ICP segment from icp.md: an "
                "established business operator/owner ($1M-25M+ revenue) fighting "
                "repetitive knowledge-work. Never developers, AI builders, or "
                "harness-obsessed audiences. The reader must match the brief."
            ),
            source=ICPC,
        ),
        EvalCriterion(
            id="one_moment",
            name="One recognized customer moment",
            description=(
                "The piece opens in (or immediately grounds in) a situation the "
                "reader recognizes from their own work — the brief's "
                "customer_moment — not in SpielOS's internal activity. Item-03: "
                "a new customer request ends with a question and nothing happens. "
                "Item-04: month-end reconciliation means clicking hundreds of rows. "
                "Item-05: a task list cannot prove the work happened."
            ),
            source=CONTENT_README,
        ),
        EvalCriterion(
            id="one_idea",
            name="Exactly one useful idea",
            description=(
                "The piece carries exactly one useful point (the brief's "
                "one_idea); every sentence, bullet, and bridge serves that point. "
                "No second topic sneaks in."
            ),
            source=COPYWRITING_EN,
        ),
        EvalCriterion(
            id="understandable_without_spielos",
            name="Understandable without knowing SpielOS",
            description=(
                "No internal production vocabulary: batch, campaign, hook, review "
                "gate, Department, Artifact, runtime, harness rule, approval "
                "record, creative signature, content dispatch. No machinery words "
                "used as product features: instruction, public record, external "
                "confirmation, returned proof, ungrounded 'live record'. A reader "
                "who has never heard of SpielOS must follow the whole piece."
            ),
            source=COPYWRITING_EN,
        ),
        EvalCriterion(
            id="buyer_language",
            name="Concrete buyer language",
            description=(
                "The piece uses the buyer's concrete words — staff time, missed "
                "details, slow replies, repeated work, delivery speed, cost, "
                "capacity, errors — at a 3rd-5th grade reading level. Workflows "
                "are explained through the real work around them, not through "
                "product abstractions."
            ),
            source=VOICE,
        ),
        EvalCriterion(
            id="sharp_opening",
            name="Sharp, immediately understood opening",
            description=(
                "The first statement is understood immediately on first read. No "
                "theatrical contrast formulas, no vague SaaS claims, no jargon "
                "gate between the reader and the idea. (The locked hook line is "
                "part of the brief and is not re-scored as writer vocabulary.)"
            ),
            source=COPYWRITING_EN,
        ),
        EvalCriterion(
            id="honest_claims",
            name="Honest, supported claims",
            description=(
                "No unsupported claim and no fabricated numbers. Every claim is "
                "supported by strategy, assets, voice, or the item's own brief "
                "and proof. No implied complete autonomy or instant "
                "company-wide transformation."
            ),
            source=VOICE,
        ),
        EvalCriterion(
            id="platform_native",
            name="Platform-native shape",
            description=(
                "Threads: real paragraphs and bullets, each bullet on its own "
                "line, and any link on its own line after the CTA. YouTube "
                "Shorts: concise description, 'Link in bio.' for a CTA, and "
                "never a UTM URL in the description. Never literal \\n or \\r "
                "markers."
            ),
            source=COPYWRITING_EN,
        ),
        EvalCriterion(
            id="flow_brevity",
            name="Flow and brevity",
            description=(
                "Short sentences, active voice, present tense where possible, no "
                "filler, no repetition. Every sentence serves the one idea; any "
                "sentence that does not strengthen the idea is removed."
            ),
            source=VOICE,
        ),
        EvalCriterion(
            id="fifth_item_reminder",
            name="Fifth-item canonical reminder",
            description=(
                "Every fifth paired idea uses the canonical short reminder "
                "'SpielOS is running itself — an AI company.' as the brand "
                "closer (NOT the opener) and is not an internal run log. The "
                "reminder may cite one public proof point. Non-fifth items do "
                "not use the reminder; CTA is optional elsewhere."
            ),
            source=VOICE,
        ),
    ),
)

EVAL_SUITES = (CONTENT_COPY_TOP10,)
