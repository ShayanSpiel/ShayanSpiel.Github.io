# Demo order — Sales Manager → Dispatch Manager (Freight Inquiry to Quote-Ready Dispatch)

- **Order id:** demo-20260829-freight-sales-dispatch
- **Type:** demo (presentation, placeholder data only — not connected to a real customer TMS/ERP)
- **Provider:** activepieces
- **Prospect:** Transport / freight & logistics demo (ICP #3 — 50–500 employees)
- **Buyer:** COO, VP Operations, Head of Billing/Revenue Management, Transportation Operations Director
- **Human loop to automate:** Freight RFQ intake — email/PDF RFQ → extract origin/destination/commodity/weight/mode/urgency → quote-ready dispatch record

## Purpose
Show a Sales Manager handing off a raw freight inquiry (pasted text + optional RFQ PDF) to the Dispatch Manager as a clean, quote-ready dispatch record — no manual retyping between inbox, PDF, and TMS.

## Demo narrative (role handover)
1. **Sales Manager** receives a freight quote request (email paste or PDF) — messy, unstructured, urgent.
2. Clicks the form, pastes the inquiry, optionally attaches the RFQ PDF.
3. SpielOS extracts **origin, destination, commodity, weight, mode, serviceType, urgency** and flags `missingQuestions`.
4. Dispatch Manager receives a **quote-ready row** in the Freight Intake table + an archived quote draft in Drive + an instant handover summary on screen.

## Requested steps (as scoped)
1. **Web Form (trigger):** Fields — Company, Contact Name, Email, Inquiry (text_area, required — paste freight request), Inquiry File (file, optional — RFQ PDF for Pixtral OCR).
2. **AI Extraction — Pixtral 12B:** Reads Inquiry text + OCR of Inquiry File (when present), outputs ONLY minified JSON with keys: origin, destination, commodity, weight, mode (FTL/LTL/Drayage/Intermodal/Parcel/Ocean/Air/Unknown), serviceType, urgency (Low/Medium/High/Critical), missingQuestions[].
3. **CODE — Normalize:** Parses JSON, trims, validates, builds canonical `handover` object; falls back to Unknown/Low + missingQuestions when fields empty.
4. **Tables — Freight Intake — Sales → Dispatch (Demo):** Creates quote-ready dispatch row (demo-simple Table that stands in for TMS/ERP). Canvas NOTE: "We use a Table instead of TMS/ERP (e.g., Oracle TMS, BluJay, MercuryGate) for demo simplicity — swap this step for your TMS Create Order." Same note in flow description.
5. **Drive — Archive:** Saves markdown quote draft (`Freight Quote — {{Company}} — {{origin}} to {{destination}}.md`) to Drive for audit / handover.
6. **Forms — Return Response:** Shows dispatch handover summary on screen with table row id + Drive link + any missingQuestions.

## ICP fit
- ICP #3: Transport, freight, logistics — loops: freight-document extraction, POD processing, billing, accessorials.
- Volume signal: high recurring RFQs, staff retyping between inbox/PDF and TMS/ERP.

## Demo data note
- Uses placeholder/demo data only, clearly labeled DEMO. Not wired to a real TMS/ERP, inbox, or domain.
- Table is demo-simple stand-in for TMS/ERP (Oracle TMS, BluJay, MercuryGate, etc.).
