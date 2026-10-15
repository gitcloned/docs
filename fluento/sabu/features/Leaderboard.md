# Leaderboard

Compare agent performance side-by-side — conversion, talk time, and rubric quality with trends.

---

## Purpose

Answers: "Who are the top performers? Is anyone trending down? Which rubric scores need coaching?"

---

## Filters

Identical to Dashboard and Calls:
- Date range (presets: Today, This Week, This Month, custom)
- Team name
- Campaign
- Min talk seconds

**Difference from other pages:** Agent filter is **multi-select** — select specific agents to compare, or leave empty to show all.

---

## Layout

### Top section — per-agent key metrics

One column per agent (card layout when ≤4 agents selected; ranked table when showing all).

| Metric | Display |
|---|---|
| Calls | Count of non-skipped calls |
| Conversion | Count + % (based on pipeline success stages) + sparkline trend |
| Avg Talk Time | Duration + sparkline trend |

Conversion = calls where `final_tag` is in any pipeline stage with `type: "success"`.
Trend = daily values over the selected date range.

### Bottom section — rubrics

One widget per rubric, same visual style as Dashboard rubric widgets.
Each widget shows all selected agents as separate rows: avg score + sparkline trend.

```
┌─ Opening Quality ──────────────────────────┐
│  Priya J.    3.8  [sparkline]              │
│  Shubham S.  3.5  [sparkline]              │
│  Chandini K. 3.1  [sparkline]              │
└────────────────────────────────────────────┘
```

---

## API

### GET /api/projects/{id}/leaderboard

**Query params** (same as dashboard):
- `date_from`, `date_to` — ISO date strings
- `team_name` — CSV
- `campaign` — CSV
- `min_talk_seconds` — int
- `agent` — CSV of agent names to include (empty = all)

**Response:**
```json
{
  "dates": ["2026-08-01", "2026-08-02", "..."],
  "agents": [
    {
      "agent_name": "Priya J.",
      "total_calls": 42,
      "converted_calls": 12,
      "conversion_rate": 0.286,
      "avg_talk_time_seconds": 204,
      "rubrics": {
        "<rubric_id>": { "avg": 3.8, "count": 40 }
      },
      "trend": {
        "conversion_rate": [0.25, 0.30, null, 0.38],
        "avg_talk_time_seconds": [180, 210, null, 204],
        "rubrics": {
          "<rubric_id>": [3.5, 3.8, null, 4.1]
        }
      }
    }
  ]
}
```

Agents sorted by `conversion_rate` descending by default.
`null` in trend arrays = no calls on that date.

---

## Decisions

| Concern | Decision |
|---|---|
| Conversion definition | pipeline success stages (same as FunnelWidget) — consistent with dashboard |
| Agent filter | multi-select CSV; empty = all agents in result set |
| Trend granularity | daily — matches existing dashboard trend |
| Rubric display | one widget per rubric, all agents in same widget — enables direct comparison |
| Sorting | by conversion_rate desc; frontend can re-sort by any column |

[← Back to index](../sales-booster.md)
