---
name: spielos-ui
description: Preserve and polish the SpielOS interface through its semantic tokens, shared components, interaction contracts, theme mappings, and visual verification workflow. Use for any SpielOS UI implementation, review, refactor, component creation, layout or sidebar change, chat/runtime presentation, form or selection behavior, loading/error/success state, icon or typography adjustment, modal/popover/drawer work, animation, accessibility, theme work, or visual polish request.
---

# SpielOS UI

Polish the existing product without reskinning it. Move repeated decisions upward into tokens and primitives, then verify their consumers and states.

## Before editing UI

Read these files:

1. `docs/design-system.md` — tokens, hierarchy, surfaces, typography, icons, rules
2. `docs/interaction-design.md` — selection, creation, loading, feedback, motion, accessibility
3. `docs/ui-quality-process.md` — migration order, change budget, done criteria

For chat/execution UI, also read:
- `docs/ui-workbench.md`
- `docs/langgraph-runtime.md`

Treat `packages/design-system` as authoritative. If code and docs disagree, fix the highest shared owner.

## Workflow

### 1. Establish evidence

- Inspect current component, shared primitives, and callers.
- Render existing UI before changing visual behavior.
- Record affected states: resting, hover, active, focus, disabled, loading, success, warning, error, empty, overflow.
- Identify active theme. Include dark, light, and monochrome verification for shared changes.

Do not infer visual quality from class names alone.

### 2. Find the owner

Choose the highest correct layer:

1. Theme palette → raw colors
2. Semantic token → repeated meaning
3. Shared primitive → repeated appearance/behavior
4. Composition component → repeated product pattern
5. Page code → unique layout and content only

Do not patch multiple pages with the same class change. Create or correct the shared owner.

### 3. Preserve product structure

- Keep established architecture, density, and layout unless change is required.
- Avoid broad rewrites, decorative redesign, gradients, oversized type, floating cards.
- Use surface hierarchy, typography, spacing, state feedback before color or borders.
- Keep each change within one named pattern.

### 4. Implement complete states

- Use shared controls and semantic tokens.
- Give every action its full state contract (resting, hover, active, focus, disabled, loading, success, error).
- Preserve drafts and user input on failure.
- Match selection control to intent: radio, checkbox, switch, navigation, attach/detach.
- Use shared icon registry and named icon-button sizes.
- Use shared motion tokens; respect reduced motion.

Runtime messages, reasoning, workflow steps must come from native events. Never fabricate in UI copy.

### 5. Verify

```bash
npm run check:ui
npm run typecheck
npm run lint
```

Run `npm test` when state/behavior changes. Run `npm run build` for shared primitives or routing changes.

Check for:
- Unexpected layout movement
- Nested or overly bright borders
- Incorrect icon scale
- Weak surface or type hierarchy
- Missing states (hover, focus, disabled, loading, error, success)
- Theme-specific contrast loss
- Stale loading after terminal state
- Keyboard traps and focus loss

### 6. Report

State which contract was fixed, which shared owner changed, which consumers verified, which checks ran.

## Rules

- Do not use raw colors, pixel typography, radius values, shadows, animation timing, or easing in app code.
- Do not import icon libraries outside the design system.
- Do not create page-local copies of shared controls.
- Do not use warning/error color for focus or selection.
- Do not represent navigation as a checkbox.
- Do not add borders where spacing or surface transition already groups.
- Do not update screenshot baselines until human reviews the change.
