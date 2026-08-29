# Spec — Demo: Sales Manager → Inventory Manager (Customer PO to Fulfillment-Ready Order)

- **Order id:** demo-20260829-po-sales-inventory
- **Type:** demo (presentation; placeholder data only — DEMO — not connected to customer systems)
- **Provider:** activepieces
- **Flow display name (MUST):** Demo — Sales Manager → Inventory Manager (Customer PO to Fulfillment-Ready Order)
- **Flow description note:** We use a Table instead of ERP (SAP, Oracle NetSuite, Xero) for demo simplicity — swap this step for your ERP Create Sales Order. + DEMO — not connected to customer systems.
- **Canvas NOTE text:** We use a Table instead of ERP/SAP/Xero for demo simplicity — swap this step for your ERP Create Sales Order.

## Trigger
- Piece: `@activepieces/piece-forms` / `form_submission` (Wait for Response = true)
- Fields:
  - `company` (text, required) — Customer company
  - `contactName` (text, required)
  - `email` (text, required)
  - `po_text` (text_area, required) — paste the whole customer PO / email body
  - `poFile` (file, optional) — PO PDF (when present, OCR via Pixtral)
- Pattern reused from Receipt flow: single paste box + optional file upload.

## Steps (linear)

1. **Trigger — PO Intake Form** — `@activepieces/piece-forms` `form_submission`
2. **AI Extraction — Pixtral 12B** — `@activepieces/piece-ai` `askAi` — model `pixtral-12b-2409`, provider `custom`, prompt extracts customer, po_number, date, items[], total from `{{trigger.po_text}}` + file URL. Output ONLY minified JSON.
3. **CODE — Normalize** — `CODE` step `normalizePO` — JSON.parse, trim, build handover, returns handoverJson + fields.
4. **Tables — Create Fulfillment-Ready Sales Order Row** — `@activepieces/piece-tables` `tables_create_record` — Table: `Sales Orders — Sales → Inventory (Demo)` (demo-simple Table that stands in for ERP) — Fields: Company=`{{trigger.company}}`, Customer=`{{code.customer}}`, PONumber=`{{code.po_number}}`, Date=`{{code.date}}`, Items=`{{code.itemsJson}}`, Total=`{{code.total}}`, RawPO=`{{trigger.po_text}}`, HandoverJSON=`{{code.handoverJson}}` — Display name includes: "We use a Table instead of ERP/SAP/Xero for demo simplicity — swap this step for your ERP Create Sales Order."
5. **Drive — Archive Order Confirmation** — `@activepieces/piece-google-drive` `drive_create_file_from_text` — File name: `Sales Order — {{trigger.company}} — {{code.po_number}}.md` — markdown handover summary.
6. **Return Response — Inventory Handover Summary** — `@activepieces/piece-forms` `return_response` — markdown with fulfillment-ready confirmation + Table id + Drive link.

## Table schema
- Table name: `Sales Orders — Sales → Inventory (Demo)`
- Fields: Company, Customer, PO Number, Date, Items (long text JSON), Total, Raw PO, Handover JSON, Drive Link, Fulfillment Ready

## Copy rule
All titles, flow name, brief/spec, and handover UI use **"Sales Manager → Inventory Manager"** role handover naming — never "PO Entry" or other technical label.
