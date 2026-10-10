# Public Website Boundary

This repository owns website pages, components, public design tokens, released
public media, website integrations, and local website build checks.
It is the buyer and lead-conversion website. The Apply funnel is its primary
conversion path. Keep reusable Skills, Departments, workflows, and private
company operations in the separate local harness.

The local company lives in `/Users/shayan/Projects/SpielOS-Website`.
The product source lives in `/Users/shayan/Projects/SpielOS1`.

Do not install a SpielOS home here. Do not create runtime state, Departments,
workflow executors, company Skills, private lead data, generation pipelines,
host adapters, or company credentials here. Company work starts from the local
home. Website changes are bounded to this repository; website builds consume
committed public snapshots and released media only.

Never read private company state from website code or follow filesystem links
into another repository. Public design system changes are website work;
production workflows consume explicit local snapshots in the company home.

Use `npm run lint`, `npm test`, and `npm run seo:check` to validate website
changes. Publishing and sending require explicit owner approval. Preserve existing files. Relocation requires explicit owner authorization;
do not delete files or create new backups. Historical relocations remain
preserved in the local company with hash receipts.

Additional website implementation guidance is in `docs/website-implementation.md` and
`docs/site-architecture.md`. These rules govern repository ownership.
