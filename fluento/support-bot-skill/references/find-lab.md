# find-lab

Find Fluento labs that match a given trait, condition, or filter. Returns matching lab IDs with supporting data.

## When to use

- "Find labs with more than 50% dropout rate"
- "Which labs had quota exhaustion errors this week?"
- "Find all labs run by school 60 in July"
- "Which labs had the chunk URL error on June 29?"
- Any question that involves searching across labs by a property or outcome

## Steps

1. Call `load_index` to see available tables and saved queries
2. Decide the filter: by error type, completion rate, school, date range, or teacher session status
3. Query `fluento.teacher_lab_session_end` for teacher-side aggregates (fast, one row per lab session)
4. If filtering by error: query `fluento.student_lab_error` grouped by `properties_lab_id`. **Filter/group by `properties_code` and exclude `SPP-4003`** (normal silence) — see `references/error-codes.md` for buckets
5. If filtering by completion rate: use `fluento_lab_completion_by_day` saved query as a base
6. Return matching lab IDs with relevant metrics

## Key tables for lab search

- `fluento.teacher_lab_session_end` — best starting point. Has per-lab totals: `properties_students_total`, `properties_students_completed`, `properties_students_errored`, `properties_session_duration_seconds`. Use `status='success'` rows.
- `fluento.student_lab_error` — to find labs with specific error types. Group by `properties_lab_id`.
- `fluento.student_lab_session_init` — to find labs by date/school with actual student entries

## Common queries

**Labs with high dropout for a school:**
```sql
SELECT
    properties_lab_id,
    properties_students_total,
    properties_students_completed,
    round((1 - properties_students_completed / properties_students_total) * 100, 1) AS dropout_pct
FROM fluento.teacher_lab_session_end
WHERE properties_school_id = <school_id>
  AND properties_status = 'success'
  AND date >= '<start_date>'
ORDER BY dropout_pct DESC
```

**Labs with a specific error:**
```sql
SELECT
    toString(properties_lab_id) AS lab_id,
    count() AS error_occurrences,
    uniqExact(properties_sa_id) AS students_affected
FROM fluento.student_lab_error
WHERE properties_school_id = <school_id>
  AND properties_message LIKE '%<error_substring>%'
  AND date = '<date>'
GROUP BY properties_lab_id
ORDER BY students_affected DESC
```

## Important gotchas

- **ClickHouse v20.12**: `GROUP BY` must list real column names, not positions or aliases
- Always use `toString(properties_lab_id)` in WHERE clauses
- `teacher_lab_session_end` has two rows per session (attempted + success) — filter on `properties_status = 'success'`
- `properties_students_not_started` is NULL on the 'attempted' row — only populated on 'success' row
- Session end not always logged — missing rows mean session may still be open

## Output format

Return a table of matching labs with their key metrics, plus a brief note on what the data shows.

## See also

- `analyze-session.md` — once you've found a lab, to deep-dive its outcome
- `session-analyser.md` — to inspect an individual run in the portal
- `glossary.md` — for lab/level/chapter and ID meanings
