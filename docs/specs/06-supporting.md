# 06 — Supporting Features (Dashboard, Todos, Files, Audit, Home)

> Parent: [`00-master-overview.md`](00-master-overview.md)
> Scope: `GET /api/v1/dashboard`, `GET /api/v1/dashboard/stats`, `GET /api/v1/student/dashboard`, `/api/v1/todos`, `/api/v1/files/upload`, `audit_logs`, the Home page.

---

## 1. Entity & Tables

### 1.1 `todos`

| Column | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK autoincrement | |
| `title` | VARCHAR(255) NOT NULL | |
| `description` | TEXT nullable | |
| `completed` | BOOLEAN NOT NULL default 0 | |
| `due_date` | DATE nullable | |
| `creator_id` | INTEGER NOT NULL → `ab_user.id` CASCADE | index — **no soft delete** |
| `created_at`, `updated_at` | DATETIME default now (+onupdate) | |

### 1.2 `audit_logs`

| Column | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK | |
| `timestamp` | DATETIME NOT NULL default now | index |
| `user_id` | INTEGER → `ab_user.id` **SET NULL** | index — the audit survives user deletion |
| `action` | VARCHAR(50) NOT NULL | index; 41 variants (§4.2) |
| `resource` | VARCHAR(100) nullable | pattern `{entity}/{name}` |
| `details` | JSON nullable | update: `{"changed": [sorted keys]}` |
| `ip_address` | VARCHAR(45) nullable | first `X-Forwarded-For` hop / `remote_addr` |
| `user_agent` | TEXT nullable | |

### 1.3 Files

**No table** — uploads are physical files only, in `app/static/uploads/`.

---

## 2. Flow: Dashboard

### 2.1 `GET /api/v1/dashboard` — `login_required` + `require_staff`

`DashboardService.admin_payload(limit=5)` — all counters are raw `COUNT(...)`:

| key | Query | Notes |
|---|---|---|
| `counts.questionCub` | `COUNT(question.name) WHERE category='cub'` | **no `status`/`disabled` filter** |
| `counts.questionScout` | same, `scout` | idem |
| `counts.questionRover` | same, `rover` | idem |
| `counts.eventActive` | `COUNT(event.name) WHERE published AND eventDeadline >= now()` | **no `disabled` filter** |
| `counts.studentActive` | `COUNT(student.user_id) WHERE status='Active'` | no `disabled` filter |
| `counts.studentInactive` | `COUNT(...) WHERE status='Inactive'` | idem |
| `counts.eventStudentToday` | `COUNT(event_student.name) WHERE created_at >= utcnow()−24 hours` | **rolling 24 hours** (the name says "Today") |
| `recentEvents` | `Event ORDER BY created_at DESC LIMIT 5` | then compute `questionCount` per row (**N+1**); `questionCount` is computed even for disabled events |
| `recentStudents` | `Student ORDER BY created_at DESC LIMIT 5` | joins User; a missing user → the row is **skipped** |

→ **200** `{ counts: {questionCub, questionScout, questionRover, eventActive, studentActive, studentInactive, eventStudentToday}, recentEvents: [EventOut+questionCount], recentStudents: [StudentOut] }`.

### 2.2 `GET /api/v1/student/dashboard` — login only

`StudentDashboardService.payload(current_user.id)`:
1. `Student` missing → `ValueError("student_not_found")` → **404**.
2. `totalPractice` = `COUNT(practice) WHERE student_id=?` (including unsubmitted) · `totalChallenge` = `COUNT(event_student) WHERE student_id=?` · `lastPractice` / `lastEvent` = latest `created_at DESC` (may be unfinished).
3. → **200** `{ category, totalPractice, totalChallenge, lastPractice: PracticeOut|null, lastEvent: EventAttemptOut|null }`.

### 2.3 `GET /api/v1/dashboard/stats` — `login_required` + `require_staff`

`DashboardService.stats_payload()` — student aggregates for the admin charts:

| key | Query | Notes |
|---|---|---|
| `totals.students` | `COUNT(student.user_id)` | all students |
| `totals.schools` | `COUNT(DISTINCT student.school) WHERE school NOT NULL AND school != ''` | the `(No school)` bucket is **not** counted as a school |
| `schools[]` | `GROUP BY COALESCE(NULLIF(school,''), '(No school)')` → `{ school, count }` | `ORDER BY count DESC, school ASC`; null **and** empty-string school collapse into `(No school)` |
| `registrations[]` | `extract('year', created_at)` `GROUP BY year` → `{ year, count }` | `ORDER BY year ASC`; **student rows** (not User), only years with data — no zero-fill. **Known limitation:** the year is read in **UTC** (`server_default=now()`), so registrations between 00:00–06:59 WIB on Jan 1 bucket into the previous year; a configured app-timezone shift is deferred |
| `categories[]` | `GROUP BY category` → `{ category, count }` | order `cub`, `scout`, `rover`, then unknown alphabetically |

→ **200** `{ totals: {students, schools}, schools: [{school, count}], registrations: [{year, count}], categories: [{category, count}] }`.

---

## 3. Flow: Todos (`/api/v1/todos`)

**RBAC:** `require_owner_or_role(todo.creator_id, "admin")` on get/update/delete — 401 `unauthorized` / 403 `forbidden`. The role is read from the local `app_role` (`_user_role()` = `app_role or "user"`).

### 3.1 `GET /` (list) — default rate

1. 401. Query: `search` (string), `completed` (**only `lower()=="true"` → True; `1`/`yes` → False**), `limit` default **100 (clamp 1..500)**, `offset ≥0` → 400 `limit_or_offset_invalid`.
2. **Visibility:** `creator_id = None when app_role=='admin' else current_user.id` → an admin sees all, everyone else sees only their own.
3. Repo filters: `creator_id`, `completed`, `title ilike %search%`; order `id DESC`.
4. → **200** `{ items: [TodoOut…] }` (no `total`).

### 3.2 `GET /<id>` → 404 `todo_not_found` → ownership 403 → **200** `TodoOut`.

### 3.3 `POST /` — rate 30/minute (any logged-in user)

`TodoCreate`: `title` 1..255 required (`title_required`); `description` optional; `completed` bool default false; `dueDate` — `None`/`""` → `None`, a bad format → `dueDate_invalid_date`.
Service create (`creator_id = current_user.id`, service commits) → audit `todo_created` `details={"title"}` → **201** `TodoOut`.

### 3.4 `PUT`/`PATCH /<id>` — rate 30/minute (both methods, one route)

1. 401 → 404 `todo_not_found` → **the ownership check runs BEFORE body validation** (not the owner → 403, not 400).
2. `TodoUpdate` (optional, `extra="ignore"`, empty → `value_no_fields_to_update`) → 400.
3. Apply `title`/`description`/`completed` when present; `dueDate` re-parsed (`""`→`None`) → commit.
4. Audit `todo_updated` `details.changed` → **200** `TodoOut`.

### 3.5 `DELETE /<id>` — rate 10/minute

401 → 404 → 403 ownership → **audit `todo_deleted` is written BEFORE the delete** → hard delete + commit → **204**.

### 3.6 `TodoOut` shape

`{ id, title, description, completed, dueDate (date iso|None), creatorId, createdAt, updatedAt }` — timestamps **without timezone** (unlike the Tantangan Bebras presenters).

---

## 4. Flow: Audit & Files

### 4.1 Audit mechanism

`services/audit.py::log(action, *, user_id, resource, details)`:
1. Build `AuditLog` (IP: first `X-Forwarded-For` hop stripped to max 45 chars, else `remote_addr[:45]`; raw `user_agent`).
2. `db.session.add` + **`flush` only — never commits** → the API caller must `db.session.commit()` immediately.
3. Any exception → swallow → `log.warning("audit log failed for action=%s: %s")` → `db.session.rollback()` **only for the audit flush** so the business transaction is not damaged.
4. Outside a request context: `user_id/IP/UA = None`.

**Placement pattern in the API:** `audit_log(...)` → `commit` (except `user_admin.update/delete` which do `commit → audit → commit`, and `user_admin.create` which does `commit → IntegrityError? rollback+409 → audit → commit`).

### 4.2 Audit coverage

**Audited (41 actions):**

| Group | Actions | resource | details |
|---|---|---|---|
| Staff auth | `register_success/failure`, `login_success/failure`, `logout` | `auth/*` | email / `reason` |
| Student auth | `student_register_success/failure`, `student_login_success/failure`, `student_logout` | `student-auth/*` | username, category / `reason` |
| Topic | `topic_created/updated/deleted/reordered` | `topic/{name}` | category / changed / count |
| Question | `question_created/updated/soft_deleted/restored/purged` | `question/{name}` | category,type / changed |
| Practice | `practice_created`, `practice_submitted` | `practice/{name}` | category / score |
| Event | `event_created/updated/soft_deleted/restored/purged` | `event/{name}` | category,n_questions / changed |
| Attempt | `event_student_started`, `event_student_submitted` | `event-student/{name}` | event / score |
| Student | `student_created/updated/soft_deleted/restored/purged/activated`, `student_import` | `student/{id}`, `student/import` | category,status / changed / inserted,updated,errors |
| User admin | `user_admin_created/updated/deleted` | `users/{id}` | role,email / changed |
| Todos | `todo_created/updated/deleted` | `todos/{id}` | title / changed |

**Not audited:** all GETs, `files/upload`, `dashboard/*`, `answer-temp` (both domains), event results, `V1/greeting`.

### 4.3 Image upload — `POST /api/v1/files/upload` — rate 30/minute

1. 401 → `unauthorized`.
2. No `file` part / empty filename → **400** `no_file`.
3. `secure_filename` → extract the extension (lowercase); **allowed**: `png, jpg, jpeg, gif, webp, svg` — anything else → **400** `file_type_not_allowed: {ext or "unknown"}` (interpolated message, contains a space).
4. Read the whole stream into memory → `> 5 MB` → **413** `file_too_large: max 5 MB`.
5. Store as `{secrets.token_hex(16)}.{ext}` in `static/uploads/` (the directory is created when needed).
6. → **201** `{ file_url: "/uploads/{name}", file_name: "{name}" }` — the `uploadFunction` contract of the frappe-ui TextEditor; served via the `GET /uploads/<path:filename>` route. No audit, no DB.

---

## 5. Error Catalog

| Code | message |
|------|---------|
| 400 | `title_required`, `dueDate_invalid_date`, `value_no_fields_to_update`, `limit_or_offset_invalid`, `no_file`, `file_type_not_allowed: {ext\|unknown}` |
| 401 | `unauthorized` |
| 403 | `forbidden` |
| 404 | `todo_not_found`, `student_not_found` (student dashboard) |
| 413 | `file_too_large: max 5 MB` |
| 429 | `rate_limit_exceeded` |

---

## 6. UI Flow (Vue)

### 6.1 Home — `/` (`home`, all roles)

- Heading "Tantangan Bebras" + a greeting.
- **Staff branch** (`isAdmin || isModerator || isCourseCreator`): a grid of 4 cards → `/question` ("Manage the Tantangan Bebras question bank"), `/event` ("Create and manage challenges"), `/student` ("Student management"), `/practice` ("Review student practice sheets").
- **Else student branch** (`isStudent`): 2 cards → `/student/practice` ("Practice questions for your category"), `/student/event` ("Available challenges").
- **Else** (unknown role): heading only, **no cards**. No API call.

### 6.2 Admin dashboard — `/dashboard`

Mount → `GET /dashboard` **and** `GET /dashboard/stats` (parallel). Counters grid (4 cards: Active Events, Active Students, Inactive Students, Attempts 24 Hours) · **Recent Events** (link `/event/{name}` + a category label; empty: "No events yet.") · **Recent Students** (name + email + status badge; empty: "No students yet.").

**Statistics** section (charts from `frappe-ui/charts`, each bound to `statsLoading` / `statsError` — built-in loading/error/empty states, so the grid keeps its shape): 2 `NumberCard` (Total Students, Total Schools) · `BarChart` "Students by School" — **top 10 + `Others` collapsed FE-side** (`frappe-ui` `maxSeries` only caps `splitBy` series, not x-axis categories) · `DonutChart` "Students by Category" (`category`/`count`, `centerLabel=Students`) · `BarChart` "Registrations by Year".

### 6.3 Student dashboard — `/student/dashboard`

Mount → `GET /student/dashboard`. "Welcome, {firstName}" · "Category: **{category}**" · 2 cards (Total Practice, Total Challenges) · buttons → `/student/practice` (solid) & `/student/event` (outline). An empty greeting when the session comes from a staff login (reads `auth.student`).

### 6.4 Todos — `/todos` (`todos`, no `meta.role` — staff-desktop sidebar only)

- Load `GET /todos` (default `limit=100`): a loading spinner / an error Alert + Retry / the list.
- Toolbar: **Add ToDo** → the create modal; search (client-side, title includes, case-insensitive); a completed select: `All statuses ''` / `Pending 'false'` / `Completed 'true'` (the server treats `completed` only as `true`→true).
- `filteredTodos` = matches search AND status.
- ListView columns: Title · Completed (`Completed` green / `Pending` orange badge) · Due date · Actions (edit ghost, delete red). Clicking a row → the edit modal.
- Modal (`components/ui/Modal.vue`, `dismissible` while not saving): Title (required), Description (textarea), Status select (`false/true`), Due date (`type=date`), inline error `saveError`.
- Save: edit → `PUT` → replace in the array + toast `ToDo "{title}" updated`; create → `POST` → `unshift` + a created toast. On failure → `saveError` + an error toast.
- Delete: `dialog.danger` "Delete ToDo" → `DELETE` → filter out + toast; on failure → toast.
- Empty state: "No todos found" + "Try adjusting filters or add a new task." + an Add ToDo button.

### 6.5 Upload in the TextEditor

`utils/textEditorUpload.ts` → a raw `fetch POST /files/upload` with `FormData` + the `X-CSRFToken` header + `credentials:'include'` → `{file_url, file_name}` → inserted into the TextEditor (unlike `fetchJson` which is JSON-only — which is why image upload works while student import does not).

### 6.6 Cross-page feedback conventions

- Success/failure: `toast.success/error` (frappe-ui).
- Destructive actions: `dialog.danger({title, message, onConfirm})`.
- Reset password: `dialog.prompt({fields:[{name:'password', validate: min 6}]})`.
- Blocking navigation out of the runner: `dialog.confirm` with custom actions (specs 03/04).
- Inline form errors: red `<p>`/`Alert` (`auth.lastError`, `error`, `submitError`, `saveError`).
