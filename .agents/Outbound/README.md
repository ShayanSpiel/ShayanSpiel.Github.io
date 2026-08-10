# Outbound operational data

This directory contains local campaign inputs, not orchestration code.

- `.env` — provider secrets and local configuration; ignored.
- `.env.example` — documented configuration contract.
- `spielos_master_outreach_database_updated_2026-08-06.xlsx` — current master
  lead database.

Runtime ledgers, provider metrics, domain state, and generated previews live
under `.spielos/state/outbound/` and `.spielos/artifacts/outbound/`. The
production code and workflows live under
`.agents/company/departments/outbound/`.
