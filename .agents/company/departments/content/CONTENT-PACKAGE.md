# ContentPackage

A ContentPackage is a run artifact, not a Department, workflow, agent, or skill.
It groups one approved brief, source evidence IDs, coordinated deliverables
(article, post, graphic, video), and publication receipts. It lives under the
goal/run artifact directory and can be rebuilt without changing the harness.

Minimum fields: `id`, `goal_id`, `run_id`, `brief`, `evidence_ids`,
`deliverables`, and `publication`.
