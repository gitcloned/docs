# error-codes — Fluento lab error taxonomy (`fluento.student_lab_error`)

The error table stores a **code** in `properties_code` (e.g. `SPP-4003`), plus `properties_message`, `properties_isrecoverable`, and `properties_details_data_fatal` (1 = fatal). **Filter and group by `properties_code`, not by message text** — messages are often NULL or vary, the code is stable.

## The rule that matters most

**`SPP-4003` (idle trigger — 5 sec of user silence) is NORMAL student behaviour. Exclude it from every error / dropout metric.** It is the single highest-volume row in the table; counting it inflates error and dropout numbers massively. Always add `AND properties_code != 'SPP-4003'` (or bucket it as Excluded) in error queries.

## Buckets (SPP codes)

| Code | Bucket | Description |
|---|---|---|
| SPP-1001 | Critical | LLM service unavailable |
| SPP-1002 | Critical | Track ended |
| SPP-1003 | Critical | Meeting has ended |
| SPP-1004 | Quota | Quota exhausted mid-activity |
| SPP-1005 | Critical | Unknown error |
| SPP-1006 | Critical | Unknown error (variant) |
| SPP-1007 | Critical | Failed to start session |
| SPP-1008 | Critical | Failed to generate report |
| SPP-2001 | Critical | Failed to get chunk/manifest URL |
| SPP-2002 | Critical | Failed to fetch scene |
| SPP-2003 | Critical | Failed to fetch lab |
| SPP-3001 | Network | Network unstable |
| SPP-3002 | Network | Network offline |
| SPP-4001 | Quota | Quota exhausted |
| SPP-4002 | Idle | Force end — idle too long |
| SPP-4003 | **Excluded** | Idle trigger — 5 sec silence (normal, not counted) |

Four counted buckets: **Critical, Quota, Network, Idle**. Excluded: SPP-4003.

## ⚠ FL-codes — investigate, not yet classified

Real data also contains a large family of codes like `FL6N6A`, `FLFZ2A`, `FLJD1A`, `FLLG4A`, … (`code_type = 'class_code'`, messages usually NULL). These are **high-volume** (collectively a large share of the table) and are **not in the SPP taxonomy above**. Do not assume their meaning. When they appear materially in results, surface them as a distinct "FL / unclassified" group and note that their classification is unconfirmed — investigate with the team or `get_context` before interpreting.

## Bucketing query (copy/adapt)

```sql
SELECT
    multiIf(
        properties_code = 'SPP-4003', 'Excluded (normal)',
        properties_code IN ('SPP-1004','SPP-4001'), 'Quota',
        properties_code = 'SPP-4002', 'Idle',
        properties_code IN ('SPP-3001','SPP-3002'), 'Network',
        properties_code IN ('SPP-1001','SPP-1002','SPP-1003','SPP-1005',
                            'SPP-1006','SPP-1007','SPP-1008',
                            'SPP-2001','SPP-2002','SPP-2003'), 'Critical',
        startsWith(properties_code, 'FL'), 'FL (unclassified)',
        'Other'
    ) AS bucket,
    count() AS occurrences,
    uniqExact(properties_sa_id) AS students
FROM fluento.student_lab_error
WHERE properties_school_id = <school_id>   -- and/or toString(properties_lab_id)=..., date filter
GROUP BY bucket
ORDER BY occurrences DESC
```
For a "real error rate", exclude SPP-4003 (and decide explicitly whether FL-codes count). Fatal vs recoverable: `properties_details_data_fatal = 1` / `properties_isrecoverable`. (ClickHouse v20.12 — GROUP BY the `multiIf(...)` expression as shown, not an alias.)
