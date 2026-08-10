# Outbound Department

The Outbound Department pursues qualified buyer conversations across email and
approved social workflows. It shares one ICP, prospect record, research dossier,
contact history, suppression policy, and outcome model.

## Workflows

- `lead-research` — discover, qualify, research, and verify prospects.
- `email-outreach` — compose, validate, approve, send, and measure email.
- `social-lead-research` — find and research LinkedIn/X prospects against ICP.
- `social-dm` — write and validate platform-native personalized DM drafts.

LinkedIn and X research must use public or owner-authorized access. The runtime
does not bulk-send unsolicited social messages. Drafts require an explicit
human/external-channel action before sending.

The company runtime owns goals and loop transitions. These workflows never run
their own scheduler, approval system, or state machine.
