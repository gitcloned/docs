# Admin — students, learning journeys and sessions

## Objective

Help an admin find any student, understand their learning progress, and inspect what happened in a session. Moving from the student list to a particular conversation should feel straightforward, with enough context to return without losing your place.

## Principles

- Start with people: show names, grades and classes, not database IDs.
- Keep the path clear: **Students → Student → Subject / topic / concept → Session**.
- Show learning state separately from session status. A concept can be “Assessing” while its latest session is “Completed”.
- Progress belongs to the student’s subject journey and is shared across classes. A class filter changes what is shown, not the underlying progress.
- Show useful summaries first. Keep raw messages, prompts and IDs available on demand.
- This version is read-only. No resetting progress, deleting records or restarting sessions.

## User journey

### 1. Find a student

Open `/admin` to see a searchable student table. Include every ERP student, even if they have never started learning.

Columns: **Name · Grade · Classes · Last active · View**.

Search by name; also accept an exact student ID for support work. Filter by class and grade. Default to recently active students, with students who have no activity last. Allow sorting by name or last activity. Use pagination and show the result count.

Show up to two class names, with “+2 more” expanding the rest. Label a parent-created personal class “Home learning”. Use “No classes yet” and “Not started” instead of blank cells.

Click the name or View to open the student. Returning restores the search, filters, page and scroll position.

### 2. Understand their learning

The student page shows their name, grade and classes, followed by **Learning**, **All sessions** and **Memories** tabs. Learning opens by default.

Inside Learning, show subjects as navigation tabs. Hide the class filter when there is only one class. When filtering by class, include only its assigned topics; explain that progress is shared across classes.

Group concepts under topic headings, with strand/unit names as secondary context. Show human-readable titles only. Each topic shows its overall status and expands into:

| Concept | Learning state | Last activity | Sessions |
|---|---|---|---|
| Completing ordered pairs | Assessing | Today, 10:20 AM | View 3 |
| Graphing solutions | Not assessed | Not started | No sessions |

Include all concepts in assigned topics, even when no progress node exists. Display those as “Not assessed”; viewing them must not create records.

Highlight the current learning activity using backend progression information. Show prerequisite detours in plain language: “Learning algebraic expressions before returning to this concept.” Make the prerequisite and return concept clickable, including those outside the assigned topic.

Keep older, unassigned progress accessible under “Previous learning”. Do not mix it into currently assigned topics or erase it from the admin view.

### 3. Find the relevant session

“View 3” opens the student’s Sessions tab filtered to that concept. “All sessions” removes the concept filter and shows sessions across subjects, including previous learning.

Columns: **Started · Subject / concept · Phase · Session status · Last activity · Turns · View**.

Default to newest first. Filter by subject, concept, phase and session status. Make active filters visible and easy to clear. Show stored statuses faithfully; do not assume a completed session means the concept is mastered.

Click a session to inspect it. Returning restores the session list and its filters.

### 4. Inspect what happened

Keep a compact context bar visible: student, concept, phase, session status, start time and last activity. Provide a Copy session link action and collapsible IDs.

Use three detail tabs:

- **Conversation:** chronological student and tutor turns, with timestamps. Render speech, writing, questions, drawings and model actions as clearly labelled blocks. Show submitted images as thumbnails that open larger; offer audio playback when a recording exists. Allow searching within the conversation and jumping to the latest turn.
- **Teaching plan:** saved steps and their statuses, including previous plan sections when the session moved between concepts. Show the saved plan, not a newly generated one.
- **Diagnostics:** saved tool calls/results, raw messages, prompts and technical events. Collapse long payloads. Show only data that was actually recorded; never imply a missing recording or event exists.

The default view is Conversation. Keep any student memories in the student-level Memories tab, with their recorded type and timestamp where available.

For a live session, provide Refresh and an optional auto-refresh toggle. Updating data must not move the reader’s scroll position; show “New activity” as a jump action instead.

## Layout and visual design

- Use the app’s cream background, forest-green accents and readable UI font. Keep this denser than the teaching canvas.
- Desktop: full-width tables, restrained spacing, clear column headings and sticky headers for long lists. Avoid large decorative cards.
- Student header → main tabs → subject tabs → topic groups. Keep these levels visually distinct.
- Show state badges with text as well as colour. Use one consistent label for each backend state.
- Session detail gets the full content area so long conversations and plans remain readable.
- On tablets, retain the main name/title and action; move secondary fields into expandable row details. Controls must work with touch and keyboard.
- Provide visible focus states, labelled filters and accessible tabs. Do not make essential actions hover-only.

## Navigation and URLs

Keep the existing admin links working:

- `/admin` — students.
- `/admin?student=:id` — student learning.
- Add `subject`, `topic`, `tab` and `concept` query parameters for selected views and filters.
- `/admin?session=:id` — session detail; resolve its student and subject context from the record.

Preserve list filters in the URL. Browser Back should behave like the visible breadcrumbs. A directly opened session link must still offer a way to its student’s page.

## Data and backend needs

- **ERP:** student directory, names, grades, class membership and personal/teacher class kind. Do not use LP journeys as the student directory: that excludes children who have not started.
- **CMS:** stable subject/topic/concept IDs, display names, hierarchy and order. Never display an ID as a title fallback; show “Title unavailable”.
- **Learning progression:** subject journeys, assignments, concept states, prerequisite links, activity, sessions, saved plans and memories.

Provide an admin read API that joins these sources and supports pagination/filtering without one browser request per student or concept. Return totals and distinguish missing data from empty data. All views use the existing admin access policy; avoid exposing student credentials or access codes.

Last activity means the latest recorded learning activity, not simply session creation time. Keep session timestamps and state transitions inspectable for diagnosing resume issues.

## Empty and error states

- No search matches: “No students match these filters” with Clear filters.
- New student: show their profile and assigned topics with “No sessions yet”.
- No assigned subjects: “No learning topics assigned yet”; keep previous sessions accessible.
- Missing curriculum labels or unavailable service: explain what could not load and offer Retry. Keep successfully loaded sections visible.
- Missing session: show “Session not found” and a link back to the student or directory.

## Acceptance checks

1. Find a student by name or class and open a session without copying IDs.
2. See a student who has never started a session.
3. Switch subjects and distinguish assigned, completed and previous learning.
4. Follow a prerequisite detour and return to the original concept.
5. Open concept-specific sessions, then all sessions, without losing student context.
6. Inspect conversation, media, saved plan and diagnostics for the same session.
7. Reload or share a URL and return to the same view; Back restores list filters.
8. Browse long lists and conversations comfortably on desktop and tablet.
9. Inspect an active session without refresh interrupting reading.
10. Viewing admin pages never creates sessions, nodes or progress changes.
