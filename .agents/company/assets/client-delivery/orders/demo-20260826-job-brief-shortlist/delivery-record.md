# Delivery record — Demo: Job Brief → Candidate Shortlist

- **Order id:** demo-20260826-job-brief-shortlist
- **Built on:** ActivePieces (flow id `BA9NmW1ddSRvBd6BQ6VPT`)
- **Demo candidate datasource:** embedded in the AI prompt — 30 candidates, 14-col schema
  (`candidates-demo.csv` is a static copy kept for reference).
- **Status:** PUBLISHED + ENABLED, valid (4/4 steps). One open item: the Drive save
  step is wired but blocked on an insufficient Google Drive OAuth scope.

## What is verified (100% working)
- Form simplification: the trigger exposes exactly two fields — `clientBrief`
  (text_area) + `jobBriefFile` (file). Confirmed via the live form metadata endpoint.
- AI extraction + matching (end-to-end with a real sample brief): submitted
  "Senior Backend Engineer, Manchester, £70–80k, Python/Django/PostgreSQL/AWS, 5+ yrs"
  → the AI extracted role/location/salary/requirements and produced a ranked top-5
  shortlist with **Ava Thompson (C-001, Senior Backend Engineer, Manchester) as Rank 1
  at 93/100**, correctly matched against the 30-candidate DB. Run `Sti9NFs75jNRe0rfVAcRq`
  (AI step succeeded).

## Open item — Drive save blocked on OAuth scope
The Save step reaches Google Drive but fails with HTTP 403
`Request had insufficient authentication scopes` (method
`google.apps.drive.v3.DriveFiles.Create`). The connection
(`igYhgyxbuxhkD3wtrsuW1`) was authorized without the file-create scope.

To finish:
1. In ActivePieces, open the Google Drive connection and **re-authorize / reconnect**,
   granting the "See, edit, create, and delete your Google Drive files" scope.
2. If reconnecting issues a NEW connection id, tell me — I'll point step_4's `auth`
   at the new id (no other change needed).
3. I will then re-run and confirm the `shortlist.md` file lands in Drive (capture the
   `webViewLink` as evidence) before marking the delivery complete.

The save step is set to `continueOnFailure = true`, so the form still returns the
shortlist even while the scope is being fixed.

## Notes
- AI model: `anthropic/claude-sonnet-4.6`.
- The web form uses `@activepieces/piece-forms` (this instance has no legacy
  `human-input` piece); `form_submission` (Wait for Response) + `return_response`
  are the equivalents of "Human Input → Web Form" / "Respond on UI".
- The 30-candidate DB is embedded in the prompt, so the demo has zero external data
  dependency (only the optional Drive save needs a connection).
