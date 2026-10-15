# lab-week-map — lab_id ↔ Level / Unit / Week (chapter)

Translates a `lab_id` to its human **(Level, Unit, Week)** and back. "Week N" = chapter N in a unit; **Week = LAB N**. Some levels also have a **Week 0** (a Unit-1 intro/setup lab). Source: flowbuilder (`https://flowbuilder-fluento.leadschool.in/lab/<lab_id>`).

> **Coverage caveat:** this map currently covers **Unit 1 only** for Levels B–G. Units 2–8 and Level H are not yet mapped — if a `lab_id` isn't in the table below, say so and (if a flowbuilder/lab-metadata tool is available) look it up rather than guessing.

## Unit 1 map

| Level | Week 0 | Week 1 (LAB 1) | Week 2 (LAB 2) | Week 3 (LAB 3) | Week 4 (LAB 4) |
|---|---|---|---|---|---|
| B | 32 | 21 | 24 | 26 | 27 |
| C | — | 23 | 22 | 25 | 28 |
| D | — | 4  | 6  | 7  | 33 |
| E | 31 | 12 | 14 | 15 | 16 |
| F | — | 17 | 18 | 19 | 20 |
| G | — | 54 | 57 | 60 | 66 |

## How to use

- **lab_id → week:** look the id up in the grid. E.g. `lab_id=15` → Level E, Unit 1, Week 3.
- **"which week is school X on?"** — there is usually **no single answer**: a school runs several levels at once (different grades). Get the school's recent lab_ids (`analyze-session.md` / the query below), map each through this grid, and report **per level** (e.g. "Level D at Week 4, Level E at Week 3, Level F at Week 4"). Do **not** collapse to one number.
- **level/week → lab_id:** read the grid the other way (e.g. Level C Week 2 → `lab_id=22`).

### Recent labs for a school (to map)
```sql
SELECT properties_lab_id AS lab_id, max(timestamp_ist) AS last_seen, uniqExact(properties_run_id) AS runs
FROM fluento.student_lab_session_init
WHERE properties_school_id = <school_id> AND date >= today() - 30
GROUP BY properties_lab_id
ORDER BY last_seen DESC
```
Then translate each `lab_id` via the grid above. (Verified: school 60 on 2026-07-13 ran labs across Levels D, E, F — Unit 1.)
