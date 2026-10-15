# analyze-session

Analyse a Fluento student lab session given a school ID, lab ID, and date. Returns completion rate, error breakdown, dropout reasons, and a plain-English conclusion.

## When to use

- "Why did students drop out of lab X on date Y?"
- "Analyse session for school 60, lab 6, June 29"
- "What happened during the fluento session today?"
- "How many students completed lab X?"
- Any question about a specific Fluento lab session's outcome

## Steps

1. Call `load_index` to orient yourself on available tables and saved queries
2. Call `get_context("fluento.student_lab_session_init")` — understand the session init table
3. Call `get_context("fluento.student_lab_error")` — understand error types before querying
4. Use the saved query `fluento_error_frequency_summary` — group errors by message, count students affected
5. Use the saved query `fluento_incomplete_students_with_reason` — find non-completers with their errors and exit method
6. Use the saved query `fluento_lab_completion_by_day` if you need completion rate over multiple days
7. Summarise: students entered, completed, errored, completion %, top errors, recoverable vs fatal

## Key tables

- `fluento.student_lab_session_init` — fires when Pipecat bot starts. Best proxy for actual lab entry. `run_id` is per-student per-session.
- `fluento.student_lab_completed` — **source of truth for completion**. Use this, not student_lab_exited.
- `fluento.student_lab_error` — error events. Key fields: `properties_message`, `properties_isrecoverable`, `properties_details_data_fatal` (1=fatal)
- `fluento.student_lab_exited` — exit events. Do NOT use for completion — known contradiction with student_lab_completed.
- `fluento.teacher_lab_session_end` — teacher-side summary: total/completed/errored/not_started counts
- `fluento.student_lab_activity_status` — per-activity lifecycle (`loaded/ready/connected/ended`) with `isllm` flag; use when the question is about individual activities or LLM-vs-non-LLM, not whole-lab outcome

## Error codes

Errors are coded in `properties_code` and grouped into buckets — see `references/error-codes.md`. **Always exclude `SPP-4003` (normal 5-sec silence) from error/dropout counts.** Legacy message strings below are still useful context:

### Known error messages to watch for

- `"No LLM Activities can be performed due to exhausted quota"` — non-recoverable, hard stop, quota issue
- `"Idle trigger fired due to 5 seconds of user silence"` — recoverable, 5s threshold too aggressive
- `"Failed to get chunk signed URL"` — caused mass dropout on Jun 29, backend issue
- `"Meeting has ended"` — fatal (properties_details_data_fatal=1), cascades after chunk URL failures
- `"Activity was forcefully stopped as user is idle for too long"` — non-recoverable idle

## Important gotchas

- **ClickHouse v20.12**: `GROUP BY` must list real column names, not positions or aliases
- `toString(properties_lab_id)` in WHERE clauses — type mismatch otherwise
- `student_lab_completed` is authoritative for completion, not `student_lab_exited.lab_state_at_exit`
- `student_lab_opened` fires on page navigation, NOT on lab entry — do not use as entry count
- `run_id` is per-student per-session, NOT shared across students

## Output format

```
School: <id> | Lab: <id> | Date: <date>
Students entered: X | Completed: Y (Z%) | Errored: W | Not started: V

Top errors:
  1. "<message>" — X occurrences, Y students affected [recoverable/fatal]
  2. ...

Conclusion: <plain-English summary of what happened and likely cause>
```

## See also

- `find-lab.md` — to first locate labs matching a condition
- `session-analyser.md` — to inspect a specific run (timer, quota, transcript, logs)
- `debug-user-issue.md` — if this is a support/hardware issue rather than an outcome analysis
- `lab-week-map.md` — to translate the lab_ids you find into Level/Unit/Week
