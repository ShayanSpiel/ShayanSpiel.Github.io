# Spec — Demo workflow: Job Brief → Candidate Shortlist

- **Order id:** demo-20260826-job-brief-shortlist
- **Type:** demo (presentation; placeholder data only — not a real client)
- **Provider:** activepieces
- **Flow id:** BA9NmW1ddSRvBd6BQ6VPT
- **Flow name:** Demo — Job Brief to Candidate Shortlist
- **Status:** published + enabled, valid (4/4 steps). Drive save step is wired but
  currently blocked by an insufficient Google Drive OAuth scope (see delivery-record.md).

## Form (simplified — one paste box + one optional upload)
Trigger: `@activepieces/piece-forms` / `form_submission` (Wait for Response = true).
- `clientBrief` (text_area, required) — paste the whole client brief; the AI extracts
  role/title, location, salary band, and must-have vs nice-to-have requirements itself.
- `jobBriefFile` (file, optional) — upload a .txt/.md brief instead of pasting.

## Steps (linear)
1. **Read Job Brief File** — `@activepieces/piece-http` / `send_request`
   HTTP GET of `{{trigger['output']['jobBriefFile'][0]['url']}}` (failureMode
   `continue_all`). Used only when a file is uploaded; ignored otherwise.
2. **AI Candidate Matching** — `@activepieces/piece-ai` / `askAi`
   Provider `{provider:"activepieces"}`, model `anthropic/claude-sonnet-4.6`,
   max tokens 4000. The 30-candidate database (14-col schema) is embedded directly
   in the prompt. The prompt extracts the vacancy facts from the pasted brief (and
   uploaded file body when present), then ranks all 30 candidates and returns a
   top-5 shortlist + recruiter summary + clean client-facing table.
3. **Save Shortlist to Drive** — `@activepieces/piece-google-drive` /
   `drive_create_file_from_text`
   Connection: google-drive (`igYhgyxbuxhkD3wtrsuW1`). Writes `shortlist.md`
   (content_type plain/text) into My Drive. `continueOnFailure = true` so the form
   still returns the shortlist if the save is blocked. Output includes `webViewLink`.
4. **Show Result** — `@activepieces/piece-forms` / `return_response`
   Returns the AI Markdown plus the saved Drive file link straight to the
   submitter's screen.

## Candidate database
Embedded in the AI prompt (30 candidates, 14 columns: id, name, title, exp, skills,
industry, location, pref, salary, notice, rtw, email, avail, notes). No external
Google Sheets / Table dependency — the demo is fully connection-free except the
optional Drive save.

## Demo experience
Open the form → paste a brief (or upload a file) → AI extracts the vacancy → ranks
all 30 candidates → top-5 shortlist renders on screen AND is saved to Google Drive.
