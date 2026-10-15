# Customer Tracker

A top-level module for managing and tracking customers across all projects.

---

## Purpose

- Central store for all customer records — imported via CSV or auto-discovered from calls
- Global schema defines what a customer is (attributes, types, unique keys)
- Each project configures which attributes to use for call-to-customer matching
- Calls auto-link to existing customers during ingest; unknown callers with a valid key become new records (stage: seeded)

---

## Scope for this build

- Data model: `customer_schema` + `customers` collections, `customer_config` on projects, `customer_id` on calls
- Backend API: schema CRUD, customer CRUD, project customer-config PATCH
- Frontend: `/customers` grid, `/customers/:id` detail, `/customers/settings` schema editor, project settings → Customer tab
- CSV import CLI
- Call ingest auto-linking (runner-side)

**Out of scope (later):** Enrichment worker, enrichment configs, multi-tenancy, project_scope on attributes.

---

## Data model

### `customer_schema` collection — one global document

```json
{
  "_id": "global",
  "description": "What a customer is in this org",
  "attributes": [
    { "name": "phone",       "type": "string",  "is_unique_key": true },
    { "name": "school_name", "type": "string",  "is_unique_key": false },
    { "name": "district",    "type": "string",  "is_unique_key": false }
  ]
}
```

| Attribute field | Type | Notes |
|---|---|---|
| `name` | string | Unique identifier — used as key in `customers.attributes` |
| `type` | string | `string`, `number`, `boolean` |
| `is_unique_key` | bool | One or more attributes that together identify a unique customer |

At least one attribute must be `is_unique_key: true`.

### `customers` collection — one doc per customer

| Field | Notes |
|---|---|
| `_id` | MongoDB ObjectId |
| `stage` | `seeded` → `enriched` → `verified` |
| `source` | `csv_upload`, `call_auto`, `manual` |
| `attributes` | `{attr_name: value}` — keys match schema attribute names |
| `created_at`, `updated_at` | timestamps |

### Stage lifecycle

```
seeded      → enriched    → verified
(created)     (AI filled)   (human confirmed)
```

- `seeded` — created during call ingest or CSV import
- `enriched` — filled by enrichment worker (future)
- `verified` — manually confirmed by user

### Projects — add `customer_config` field

```json
{
  "customer_config": {
    "match_attributes": ["phone"]
  }
}
```

`match_attributes` — list of schema attribute names used to look up / deduplicate customers during call ingest. One value per name must be present in the CDR for linking to happen.

### Calls — add `customer_id` field

`customer_id: ObjectId | null` — set during ingest when a customer is found or created.

---

## API

### Customer Schema

| Method | Path | Auth | Notes |
|---|---|---|---|
| `GET` | `/api/customer-schema` | Firebase / any | Get the global schema |
| `PUT` | `/api/customer-schema` | Firebase / site-admin+ | Replace schema (attributes list) |

### Customers

| Method | Path | Auth | Notes |
|---|---|---|---|
| `GET` | `/api/customers` | Firebase / any | List — params: `stage`, `source`, `search` |
| `POST` | `/api/customers` | Firebase / any | Create manually |
| `GET` | `/api/customers/{id}` | Firebase / any | Get single customer |
| `PUT` | `/api/customers/{id}` | Firebase / any | Update attributes or stage |
| `DELETE` | `/api/customers/{id}` | Firebase / site-admin+ | Delete |

### Project customer config

| Method | Path | Auth | Notes |
|---|---|---|---|
| `PATCH` | `/api/projects/{id}/customer-config` | Firebase / project-admin | Save match_attributes |

---

## Call ingest auto-linking

Runs inside the runner's ingest loop after writing the call record.

```
1. Load project.customer_config.match_attributes  (e.g. ["phone"])
2. Get CDR value for each match attribute
   └── if any match attribute value is blank → skip, set customer_id = null
3. Query customers where attributes.<attr> = <value> for all match attributes
   ├── Found → set customer_id = existing customer._id
   └── Not found → create customer (stage=seeded, source=call_auto)
                   set customer_id = new customer._id
4. PATCH call record with customer_id via backend API
```

No customer is created if any match attribute value is missing from the CDR.

---

## CSV import CLI

```bash
python workers/customers/import_csv.py \
  --file customers.csv \
  --env production \
  --map phone=PhoneNumber,school_name="School Name",district=District
```

- `--map` maps schema attribute names to CSV column headers
- Deduplicates on `is_unique_key` attributes before inserting
- Existing customers (matched by unique key) are updated, not duplicated
- Prints summary: created / updated / skipped

---

## Frontend

### `/customers` — Grid view

- Table with dynamic columns from schema attributes
- Filters: `stage`, `source`, free-text search
- Click row → `/customers/:id`

### `/customers/:id` — Customer detail

- All attributes editable inline
- Stage pill with manual transition controls
- Linked calls list (calls where `customer_id` = this customer)

### `/customers/settings` — Schema editor

- Edit description
- Add / edit / remove attributes (name, type, is_unique_key)
- Reorder attributes (display order)
- Validation: at least one `is_unique_key` must exist

### Project settings → "Customer" tab

- Multi-select: which schema attributes to use as match keys for this project's ingest

---

## Files to create / modify

| File | Change |
|---|---|
| `backend/db.py` | Add `get_customer_schema_col()`, `get_customers_col()` |
| `backend/models.py` | Add `CustomerAttribute`, `CustomerSchema`, `CustomerRecord`, `CustomerConfig` models |
| `backend/routers/customers.py` | New — customer CRUD |
| `backend/routers/customer_schema.py` | New — schema GET/PUT |
| `backend/routers/projects.py` | Add `PATCH /{id}/customer-config` endpoint |
| `backend/main.py` | Register new routers |
| `workers/runner/runner.py` | Add customer linking in ingest loop |
| `workers/customers/import_csv.py` | New — CSV import CLI |
| `frontend/src/customers/CustomersPage.tsx` | New |
| `frontend/src/customers/CustomerDetailPage.tsx` | New |
| `frontend/src/customers/CustomerSettingsPage.tsx` | New |
| `frontend/src/projects/ProjectForm.tsx` | Add Customer tab |
| `frontend/src/components/Layout.tsx` | Add Customers nav link |
| `frontend/src/App.tsx` | Add `/customers` routes |

---

## Decisions

| Concern | Decision |
|---|---|
| Multi-tenancy | Skipped — single global schema, add org_id later via migration |
| project_scope on attributes | Skipped — all attributes visible everywhere for now |
| Enrichment worker | Out of scope — separate future feature |
| Customer matching | Per-project `match_attributes` config; skip if CDR value blank |
| Unique key | Defined on attribute (`is_unique_key`); can be composite |
| CSV import | CLI tool — not a frontend file upload |
| Call linkage timing | During ingest (not analysis) — only CDR data needed |
| customer_id on calls | Nullable field; null = no customer linked |

[← Back to index](../sales-booster.md)
