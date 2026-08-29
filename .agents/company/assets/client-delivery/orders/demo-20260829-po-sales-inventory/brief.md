# Demo order — Sales Manager → Inventory Manager (Customer PO to Fulfillment-Ready Order)

- **Order id:** demo-20260829-po-sales-inventory
- **Type:** demo (presentation, placeholder data only — not connected to a real customer ERP)
- **Provider:** activepieces
- **Prospect:** Mid-market manufacturers + Industrial distributors demo (ICP #1 & #2 — 50-500 employees)
- **Buyer:** COO, VP Operations, Supply Chain Director, Procurement Director
- **Human loop to automate:** Sales-order entry — customer PO (PDF/email/spreadsheet) → extract customer/SKU/qty/price → validate → fulfillment-ready sales order in ERP

## Purpose
Show a Sales Manager handing off a raw customer PO (pasted text + optional PDF) to the Inventory Manager as a clean, fulfillment-ready sales order — no manual retyping between inbox, spreadsheet, and ERP.

## Demo narrative (role handover)
1. **Sales Manager** receives a customer purchase order (email paste or PDF) — messy, unstructured.
2. Clicks the form, pastes the PO, optionally attaches the PDF.
3. SpielOS extracts **customer, PO number, date, SKUs, quantities, prices, total** and validates against price-list Table.
4. **Inventory Manager** receives a **fulfillment-ready row** in the Sales Orders table + an archived order confirmation in Drive + an instant handover summary on screen.

## Requested steps (as scoped)
1. **Web Form (trigger):** Fields — Company (text, required), Contact Name, Email, PO Text (text_area, required — paste PO), PO File (file, optional — PO PDF for Pixtral OCR).
2. **AI Extraction — Pixtral 12B:** Reads PO Text + OCR of PO File (when present), outputs ONLY minified JSON with keys: customer (string), po_number (string), date (string), items (array of {sku, description, qty, unit_price}), total (string).
3. **CODE — Normalize:** Parses JSON, trims, builds canonical handover object.
4. **Tables — Sales Orders — Sales → Inventory (Demo):** Creates fulfillment-ready sales order row (demo-simple Table that stands in for ERP/SAP/Xero). Canvas NOTE: "We use a Table instead of ERP/SAP/Xero for demo simplicity — swap this step for your ERP Create Sales Order." Same note in flow description and step display name.
5. **Drive — Archive:** Saves markdown order confirmation to Drive.
6. **Forms — Return Response:** Shows inventory handover summary on screen.

## ICP fit
- ICP #1 + #2: Industrial distributors & mid-market manufacturers — loops: sales-order entry, RFQ, PO, inventory checks, ERP movement.
- Volume signal: high recurring POs, staff retyping between email/PDF and ERP.

## Demo data note
- Uses placeholder/demo data only, clearly labeled DEMO. Not wired to a real ERP, inbox, or domain.
- Table is demo-simple stand-in for ERP (SAP, Oracle NetSuite, Xero, etc.).
