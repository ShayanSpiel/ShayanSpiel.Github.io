# Change Report — Persian System Redesign (v2)

## Current file inventory

| File | Path | Purpose |
|---|---|---|
| SpielOS ICP | `.agents/spielos-icp.md` | Single source of truth for customer profile (shared by EN and FA) |
| Persian glossary | `.agents/skills/translation-fa/persian-glossary.md` | Terminology source of truth |
| Translation skill | `.agents/skills/translation-fa/SKILL.md` | Localization and Persian-writing system |
| English copywriting | `.agents/skills/copywriting-en/SKILL.md` | EN content creation from work sessions |
| Persian copywriting | `.agents/skills/copywriting-fa/SKILL.md` | FA content creation from work sessions |
| Quality test suite | `.agents/skills/translation-fa/quality-test-suite.md` | 44 examples with failure analysis |
| Change report | `.agents/skills/translation-fa/CHANGE-REPORT.md` | This file |

## What was removed

1. **Old `glossary.md`** (90 lines) — superseded by `persian-glossary.md` (370 lines). Contained mixed terminology, voice rules, and quality tests. Replaced by a clean three-category glossary.

## What was preserved

All existing terminology mappings, banned translations, voice rules, UX surface rules, showcase/RTL rules, and quality gates from the previous version.

## What was added in v2

### 1. `spielos-icp.md`

The single source of truth for both English and Persian copywriting. Contains:

- Primary customer definition (founder-led startups, technical/product-minded founders)
- Current situation and common problems
- Desired outcomes
- Core product promise
- Relevant company functions
- Persian and international market definitions
- Awareness levels (problem-aware, solution-aware, product-aware)
- Buying triggers
- Primary objections
- Not-the-ICP exclusions
- Superseded positioning (Session-as-Content is no longer the primary ICP)

### 2. `copywriting-en/SKILL.md`

New English copywriting skill. Covers:

- ICP summary (operational)
- All surfaces (homepage, features, use-cases, founder story, notes, announcements, waitlist, X, LinkedIn, email, CTAs, product explanations, technical education)
- English voice (direct, intelligent, founder-written)
- Banned or scrutinized phrases (revolutionary, cutting-edge, seamless, powerful, next-generation, etc.)
- Reader-context rule
- Work sessions are evidence (not structure)
- ICP simulation
- Product truth versus customer language
- Awareness levels
- Long-form article structure
- Titles, CTAs, evidence over slogans
- Quality gates

### 3. Updated `copywriting-fa/SKILL.md`

Full canonical ICP rules added:

- References `spielos-icp.md` as single source of truth
- Operational ICP summary in English and Persian
- Awareness levels with Persian-specific examples
- Buying triggers in Persian
- Primary objections in Persian
- Persian-specific simulation questions (how would an Iranian founder describe this aloud, which terms are natural, which need explanation, which search phrases sound artificial)
- Shared bilingual content rule
- Quality gates

### 4. Updated `translation-fa/SKILL.md`

Added reference to `spielos-icp.md` in the reference files section.

### 5. Updated `persian-glossary.md`

Added reference to `spielos-icp.md` at the top of the file.

### 6. Expanded quality test suite

From 25 examples to 44 examples across four parts:

- **Part 1: Persian translation tests** (P1–P20) — context recovery, voice, sentence completeness, glossary compliance, register, collocations, technical terms
- **Part 2: English copywriting tests** (E1–E10) — context-free openings, session logs, feature inventories, internal jargon, awareness levels, generic AI copy, unsupported claims, overwritten slogans, product truth, CTAs
- **Part 3: Bilingual comparison tests** (B1–B10) — same evidence expressed naturally in both languages, showing structural independence
- **Part 4: Persian copywriting tests** (F1–F4) — Iranian founder voice, technical term dumping, artificial search phrases, sentences dependent on English source

Each example includes: source material, ICP segment and awareness level, weak output, why it fails, correct output, and rule being tested.

## Architecture

```
.agents/
├── spielos-icp.md                    ← ICP (canonical, shared truth)
├── skills/
│   ├── translation-fa/
│   │   ├── SKILL.md                  ← Translation/localization system
│   │   ├── persian-glossary.md       ← Terminology
│   │   ├── quality-test-suite.md     ← 44 test cases
│   │   └── CHANGE-REPORT.md          ← This file
│   ├── copywriting-en/
│   │   └── SKILL.md                  ← English content creation
│   └── copywriting-fa/
│       └── SKILL.md                  ← Persian content creation
└── Outbound/
    └── spielos-icp.md                ← Outbound execution (implements canonical)
```

All skills reference `../../spielos-icp.md` (canonical, top-level). The ICP is not duplicated in any skill file — it is read from the single source of truth.

## v3 update (2026-08-08)

- ICP moved from `.agents/skills/spielos-icp.md` to `.agents/spielos-icp.md` (canonical, top level).
- ICP replaced: primary buyer is now the owner/CEO/COO/senior operator of an established online business or service provider ($1M–$25M+ revenue) with repetitive knowledge-work — not the technical-founder ICP.
- All reference paths updated; the technical-founder ICP is superseded.

## Failure modes covered

### Translation (existing, preserved)

- Wrong product terminology
- Banned translations
- Corporate filler words
- Subject-verb disagreement
- Missing context
- Grammar-for-intention translation
- Passive/unclear actor-action
- Hiding actions behind nouns
- Architecture before outcomes
- Incomplete sentences

### Translation (new in v1)

- Grammatically correct but meaningless Persian
- Literal English sentence structures
- Context-free openings
- Technical word dumping
- Noun-phrase rules (fragments instead of instructions)
- Register mixing
- Obscure vocabulary

### Copywriting (new in v2)

- Session-log articles (chronological instead of reader-centered)
- Feature inventories presented as positioning
- Internal jargon used as customer language
- Wrong awareness level for the surface
- Generic AI language
- Unsupported claims
- Overwritten slogans
- False product claims
- Vague CTAs
- English structural copying into Persian
- Artificially translated search phrases
- Bureaucratic register in Persian
- Technical term dumping in Persian
- Sentences dependent on English source
- Iranian founder voice violations
