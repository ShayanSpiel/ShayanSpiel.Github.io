# AI-first company presentation

The current presentation is `/ai-transformation/`; the Persian RTL equivalent is
`/fa/ai-transformation/`. The preserved classic is available directly at
`/ai-transformation-classic/` and `/fa/ai-transformation-classic/`.

The 60-slide current edition retains the classic chapter structure and the
Goal → Observe → Decide → Act → Evaluate framework. Five repetitive beats are
omitted, and four practical beats show a workflow brief, Activepieces MCP build,
acceptance cases and repair. Ordinary concepts retain side headings; the
Activepieces editor is a full-width exception. Top controls provide restart.

All dashboards, runs and evaluation numbers are illustrative, not production
claims. The Activepieces editor is a visual reconstruction from public references,
not a connected editor. MCP names follow https://www.activepieces.com/docs/mcp/tools.
Editor reference: https://www.activepieces.com/blog/how-to-build-ai-sales-agents-for-cold-email-outreach.
LangSmith references: https://docs.langchain.com/langsmith/view-traces and
https://docs.langchain.com/langsmith/compare-experiment-results.

The finale uses the released original signature video; reduced motion holds its
final frame. Its baked English tagline is preserved in the Persian edition.
No private company runtime state is loaded.

Validation: `npm run lint`, `npm test`, `npm run seo:check`, and
`DECK_AUDIT_ORIGIN=http://localhost:4321 node test/transformation-deck-audit.mjs`.
Set `DECK_AUDIT_PATH=/fa/ai-transformation/` for RTL. The browser audit checks
every slide at five viewport sizes, tile overlap, overflow, keyboard navigation,
history and reduced motion. Final English and Persian audits each passed 300 captures.
