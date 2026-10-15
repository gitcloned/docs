# Module — Teacher Context

Knows who is logged in on this device and what each teacher teaches. Fully local — no network calls.

---

## Function

- Store and retrieve teacher accounts (JWT, school info)
- Store and retrieve each teacher's class/division/subject assignments (self-declared by the teacher)
- Tell other modules: "Teacher A teaches these subjects; Teacher B teaches these"

**Interface:**
```
getAllTeachers(): List<TeacherAccount>
getActiveTeacher(): TeacherAccount?
getAssignmentsForTeacher(teacherId): List<TeacherClassAssignment>
getAllAssignments(): Map<TeacherAccount, List<TeacherClassAssignment>>
addTeacher(credentials): TeacherAccount
setActiveTeacher(teacherId)
saveAssignments(teacherId, assignments: List<TeacherClassAssignment>)
removeAssignment(teacherId, classId, division, subjectId)
```

---

## Non-functional requirements

- **Fully offline:** all reads and writes are local Room DB only. No network dependency.
- **Persists across restarts:** Room DB ensures data survives app kills and reboots.
- **Multi-teacher safe:** teacher accounts are independent rows. One teacher's data never overwrites another's.
- **Immediate consistency:** any write is readable in the same session without delay.

---

## Algorithm

**Adding a teacher (first login or "add account"):**
```
1. Auth API call (handled outside this module — by Login screen)
2. On success: insert TeacherAccount row with JWT and school fields
3. If first teacher: set isActive = true
4. Navigate to class setup screen
```

**Teacher switching:**
```
1. Set isActive = false on current active teacher
2. Set isActive = true on selected teacher
3. Emit teacher-changed event → Sync Orchestrator triggers
```

**Assignment update:**
```
1. Delete existing TeacherClassAssignment rows for this teacher
2. Insert new rows for each class+division+subject combination
3. Emit assignments-changed event → Sync Orchestrator triggers
```

---

## Room DB

### `TeacherAccount` (existing table)

| Field | Type | Notes |
|---|---|---|
| id | String | `schooluserid` from auth response |
| name | String | Display name |
| jwt | String | `user_token` from auth response (`su[0].user_token`) |
| schoolId | String | `su[0].schoolid` |
| academicYearId | String | `su[0].academicyearid` |
| deviceToken | String | `token` from auth response |
| isActive | Boolean | Which teacher is currently selected |

### `TeacherClassAssignment` (existing table)

Teacher's self-declared teaching load. Set on the Class/Division/Subject setup screen.

| Field | Type | Notes |
|---|---|---|
| teacherId | String | FK → TeacherAccount.id |
| classId | String | Class identifier from Realm |
| division | String | Division/section (e.g. "A", "B") |
| subjectId | String | Subject identifier from Realm |

One row per class+division+subject combination. A teacher with 3 classes and 2 subjects each = 6 rows.

---

## Realm DB

None. This module has no dependency on Realm.

---

## Dependencies

- Reads from: `TeacherAccount`, `TeacherClassAssignment` Room tables
- Writes to: `TeacherAccount`, `TeacherClassAssignment` Room tables
- Called by: Sync Orchestrator, Login screen, Class Setup screen
- Read by: Priority Engine

[← Back to index](modules.md)
