# Spec — Demo: Sales Manager → Dispatch Manager (Freight Inquiry to Quote-Ready Dispatch)

- **Order id:** demo-20260829-freight-sales-dispatch
- **Type:** demo (presentation; placeholder data only — DEMO — not connected to customer systems)
- **Provider:** activepieces
- **Flow display name (MUST):** Demo — Sales Manager → Dispatch Manager (Freight Inquiry to Quote-Ready Dispatch)
- **Flow description note:** We use a Table instead of TMS/ERP (e.g., Oracle TMS, BluJay, MercuryGate) for demo simplicity — swap this step for your TMS Create Order. + DEMO — not connected to customer systems.
- **Canvas NOTE text:** We use a Table instead of TMS/ERP (e.g., Oracle TMS, BluJay, MercuryGate) for demo simplicity — swap this step for your TMS Create Order.

## Trigger
- Piece: `@activepieces/piece-forms` / `form_submission` (Wait for Response = true)
- Fields:
  - `company` (text, required) — Shipper / prospect company
  - `contactName` (text, required)
  - `email` (text, required) — contact email
  - `inquiry` (text_area, required) — paste the whole freight quote request / email body
  - `inquiryFile` (file, optional) — RFQ PDF (when present, OCR via Pixtral)
- Pattern reused from Receipt flow 9cC7eE7Q0btMTzl99R4rt: single paste box + optional file upload.

## Steps (linear, 6 steps including trigger)

1. **Trigger — Freight Inquiry Form** — `@activepieces/piece-forms` `form_submission`
   Display name: "Freight Inquiry — Sales → Dispatch"
2. **Read Inquiry File (optional)** — `@activepieces/piece-http` `send_request` OR direct file-url passthrough to AI
   - GET `{{trigger['output']['inquiryFile'][0]['url']}}` if file present; failureMode `continue_all`.
   - Used only when file uploaded; else skipped. Content fed to Pixtral as image/pdf url.
3. **AI Extraction — Pixtral 12B** — `@activepieces/piece-ai` `askAi`
   - Provider: `activepieces`, model: `pixtral-12b-2409`
   - Prompt: extracts origin, destination, commodity, weight, mode, serviceType, urgency, missingQuestions from `{{trigger.inquiry}}` + file content. Prompt MUST instruct: "Output ONLY minified JSON with keys: origin, destination, commodity, weight, mode (FTL/LTL/Drayage/Intermodal/Parcel/Ocean/Air/Unknown), serviceType, urgency (Low/Medium/High/Critical), missingQuestions (array). No markdown, no explanation."
   - Input includes: Inquiry text = `{{trigger.inquiry}}`, File URL = `{{step_1.body or trigger.inquiryFile URL}}`
4. **CODE — Normalize** — `CODE` step `normalizeFreight`
   - Export: `code` fn, inputs: `rawJson` = `{{step_2.response}}` or `{{step_pixtral.response}}`
   - Logic: JSON.parse, trim strings, default missing to "", mode enum validate, urgency enum validate, missingQuestions ensure array, build `handover` JSON string. Returns `{ handoverJson, origin, destination, commodity, weight, mode, serviceType, urgency, missingQuestions }` with minified JSON + individual fields for downstream.
5. **Tables — Create Quote-Ready Dispatch Row** — `@activepieces/piece-tables` `tables_create_record` (or insert)
   - Table: `Freight Intake — Sales → Dispatch (Demo)` (demo-simple Table that stands in for TMS/ERP)
   - Fields: Company=`{{trigger.company}}`, Contact=`{{trigger.contactName}}`, Email=`{{trigger.email}}`, Origin=`{{code.origin}}`, Destination=`{{code.destination}}`, Commodity=`{{code.commodity}}`, Weight=`{{code.weight}}`, Mode=`{{code.mode}}`, ServiceType=`{{code.serviceType}}`, Urgency=`{{code.urgency}}`, MissingQuestions=`{{code.missingQuestions joined}}`, RawInquiry=`{{trigger.inquiry}}`, HandoverJSON=`{{code.handoverJson}}`, CreatedAt=`now`
   - Description/note on step: "We use a Table instead of TMS/ERP (e.g., Oracle TMS, BluJay, MercuryGate) for demo simplicity — swap this step for your TMS Create Order."
6. **Drive — Archive Quote Draft** — `@activepieces/piece-google-drive` `drive_create_file_from_text`
   - Connection: `google-drive` (resolve at build time)
   - File name: `Freight Quote — {{trigger.company}} — {{code.origin}} to {{code.destination}}.md`
   - Content: markdown handover summary (Company, Contact, Origin/Destination, Commodity/Weight/Mode/Service/Urgency, Missing Questions, Raw Inquiry excerpt, Handover JSON)
   - `continueOnFailure = true` so form still returns even if Drive scope blocked.
7. **Return Response — Dispatch Handover Summary** — `@activepieces/piece-forms` `return_response`
   - Body (markdown): `# Sales → Dispatch: Quote-Ready\n**Company:** ...\n**Lane:** origin → destination\n**Commodity/Weight:** ...\n**Mode/Service:** ...\n**Urgency:** ...\n**Missing:** ...\n**Table row id:** {{tables.id}}\n**Drive:** {{drive.webViewLink}}\n**Handover JSON:** {{code.handoverJson}}`
   - Shows full handover + Drive link + Table confirmation straight to submitter.

## Table schema
- Table name: `Freight Intake — Sales → Dispatch (Demo)`
- Fields (text unless noted): Company, Contact Name, Email, Origin, Destination, Commodity, Weight, Mode, ServiceType, Urgency, MissingQuestions (text), RawInquiry (long text), HandoverJSON (long text), CreatedAt (date/text), DriveLink (text), QuoteReady (checkbox/text = Yes)

## Drive archive
- Folder: My Drive (or `SpielOS Client Delivery/Demos/...` if available)
- File: markdown, content_type `text/plain` or `text/markdown`
- Evidence: `webViewLink` captured.

## Demo experience
Open the form → paste a freight RFQ (e.g., "Need FTL quote, Houston TX → Chicago IL, 18 pallets electronics, 22,000 lbs, expedited") + optionally upload RFQ PDF → Pixtral extracts lane/commodity/mode/urgency → CODE normalizes → Table row created (quote-ready) → Drive markdown saved → Handover summary renders on screen with Table id + Drive link.

## Verification (100% before delivery)
- Form fields verified via live form metadata.
- Sample RFQ submitted end-to-end (or AI logic exercised with hardcoded sample + same prompt) — capture AI JSON output.
- Table row confirmed (record id + fields).
- Drive file confirmed (webViewLink) — if scope blocked, note remediation.
- Return response markdown inspected.

## Copy rule
All titles, flow name, brief/spec, and handover UI use **"Sales Manager → Dispatch Manager"** role handover naming — never "Freight RFQ Intake" or other technical label.
