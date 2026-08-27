# Client Delivery — order registry & folder conventions

Lean, scalable order storage for the Client Delivery Department. This local
folder is the company-memory source of truth; the Google Drive + Sheets
Connections mirror it online (see the `client-delivery` department skill).

## Local tree

```
.agents/company/assets/client-delivery/
  README.md            # this file
  registry.csv         # one row per order (id,type,provider,client,status,links)
  orders/
    wf-YYYYMMDD-<slug>/ # real client build
      brief.md  spec.md  delivery-record.md
    demo-YYYYMMDD-<slug>/ # demo / presentation build
      brief.md  spec.md  delivery-record.md
```

## Rules

- One folder per order; order id is identical in the folder name, the
  ActivePieces flow name, the local `registry.csv` row, and the Drive row.
- `real` orders use real customer data where scope allows; `demo` orders use
  placeholder/demo data only, labeled `DEMO` in the flow name and description.
- A delivery is complete only when local folder + Drive mirror + both
  registries agree.
