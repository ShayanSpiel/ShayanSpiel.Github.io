# Karwise website

English at https://spielos.xyz/; Persian at /fa/.

The committed public/ directory is the self-contained website snapshot. npm ci && npm run build copies it to dist/ and verifies entry pages and FormSubmit contact wiring. GitHub Pages publishes dist/ on main. Historical Astro sources remain preserved but are not the serving build. Public releases never contain company runtime state or private credentials.

Every canonical page needs its own generated social image before the build can pass. See [the OG image workflow](docs/og-image-workflow.md).
