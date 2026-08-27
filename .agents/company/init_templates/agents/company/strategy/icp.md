# SpielOS Ideal Customer Profile

This is the canonical ICP. Every department, skill, lead score, and piece of copy reads this file. Do not redefine it elsewhere.

## Who it is

The five priority segments below are the only target groups.

## Priority segments

### 1. Industrial distributors and wholesalers

- 30-250 employees; $10M-$150M revenue; transaction volume is growing faster than headcount.
- Order-to-ERP loop: customer PO, RFQ, spreadsheet, PDF, or email -> extract -> customer/SKU/price checks -> sales order -> exception handling -> confirmation.
- Buyers: COO, VP or Director of Operations, Head of Customer Service, Sales Operations, or GM.
- Proof: Ashling reports nearly 1M automated orders per year, 40% fewer manually handled orders, and $5M annual value.

### 2. Mid-market manufacturers

- 50-500 employees; $20M-$250M revenue; established operations spanning ERP, purchasing, production, suppliers, and customer orders.
- Loops: sales-order entry, RFQs, purchase orders, supplier documents, inventory checks, back-order notices, and ERP data movement.
- Buyers: COO, VP Operations, Supply Chain Director, Procurement Director, or Operations Excellence lead.
- Proof: 80% straight-through processing across 1.5M+ material reports annually.

### 3. Transport, freight, and logistics companies

- Carriers, 3PLs, LTL operators, and logistics firms; 50-500 employees; $10M-$250M+ revenue.
- Loops: freight-document extraction, POD processing, billing, accessorial-charge detection, invoices, customer updates, claims, and revenue-leakage checks.
- Buyers: COO, VP Operations, CFO, Head of Billing or Revenue Management, or Transportation Operations Director.
- Proof: EXL reports $15M in annual revenue leakage prevented for a large US transportation company. LTL accessorial revenue is often missed.

### 4. Food and CPG manufacturers and distributors

- 50-500 employees; $20M-$250M revenue; high order volume through email, PDFs, portals, EDI exceptions, or spreadsheets.
- Loops: customer-order intake, validation, ERP entry, deductions, invoices, inventory checks, and confirmations.
- Buyers: COO, Customer Service Director, Order Management Director, Sales Operations, or Supply Chain lead.
- Proof: Ashling reports a 75% reduction in manual order processing and 60+ staff hours saved per week.

### 5. Mid-market finance teams with heavy accounts payable

- Multi-location or transaction-heavy companies; 100-1,000 employees; $25M-$500M revenue; hundreds or thousands of invoices each month.
- Invoice-to-pay loop: invoice arrives -> extract -> vendor/PO match -> validate -> route exception -> approve -> ERP -> payment -> reconcile.
- Buyers: CFO, Controller, Head or Director of AP, Finance Operations Director, or Shared Services lead.
- Proof: Genpact reports $200M+ in AP automation contract value in under a year and up to 80% touchless processing.

## Qualification signal

Prioritize in the order above. A qualified account has high recurring transaction volume, staff moving information between email or documents and an ERP, and a measurable cost, capacity, speed, or revenue impact.

## Who it is NOT

The exclusions below are disqualifying.

## Exclusions and evidence gates

- Exclude AI companies or agencies selling AI, dev shops, pre-revenue firms, free-mail contacts, and companies outside the segment size limits.
- Name a senior operator from the segment buyer list. A role inbox is not a primary contact.
- Use a personal corporate-domain email and a public or verified contact.
- Record citable overflow or capacity-strain evidence with its source URL.
- Name one manual loop as `research_fact`, then state its pain hypothesis and content hook.

## Scope note

Outbound execution details belong in `.agents/company/departments/outbound/strategy.md`. This file owns the buyer, exclusions, segment order, and qualification signal.
