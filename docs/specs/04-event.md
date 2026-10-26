# 04 — Event (Challenge) — Admin & Student

> Parent: [`00-master-overview.md`](00-master-overview.md)
> Scope: `event`, `event_question`, `event_student` + children, API `/api/v1/event` (admin) and `/api/v1/student/event` (student), the frontend event runner.

---

## 1. Entity & Tables

### 1.1 `event`

| Column | Type | Notes |
|-------|------|-------|
| `name` | VARCHAR(140) PK | slug of `eventName` |
| `eventName` | VARCHAR(255) NOT NULL | |
| `category` | VARCHAR(20) NOT NULL | index |
| `timeLimit` | INTEGER NOT NULL default 60 | **minutes**; DTO validation 1..600 |
| `eventDeadline` | DATETIME NOT NULL | index — the end bound; stored from the client ISO string |
| `published` | BOOLEAN NOT NULL default 0 | index — draft ↔ published |
| `description` | TEXT nullable | |
| `creator_id` | INTEGER → `ab_user.id` SET NULL | |
| `disabled`, `disabled_at` | BOOLEAN default 0 / DATETIME | soft delete (index) |
| `created_at`, `updated_at` | DATETIME default now | |

### 1.2 `event_question`

`id` PK autoincrement · `event_id` → `event.name` CASCADE (index) · `question_id` → `question.name` **RESTRICT** · `idx` INTEGER default 0 · **UNIQUE `(event_id, question_id)`**. — order = the client's `questionsId` order.

### 1.3 `event_student` (attempt header)

| Column | Type | Notes |
|-------|------|-------|
| `name` | VARCHAR(140) PK | `student-{student_id}-{event_name}-{unix_ts}` — no uniqueness check |
| `student_id` | INTEGER → `ab_user.id` CASCADE (index) | |
| `event_id` | VARCHAR(140) → `event.name` CASCADE (index) | |
| `score` | INTEGER nullable | final score |
| `timeLimit` | INTEGER nullable | seconds |
| `startedAt` / `finishedAt` | DATETIME nullable | finished ≠ null = terminal |
| `created_at`, `updated_at` | DATETIME | implicit index via ordering |

**UNIQUE `(student_id, event_id)`** → one attempt per student per event.

### 1.4 `event_student_question`

`id` PK · `event_student_id` → `event_student.name` CASCADE (index) · `event_question_id` → **`event_question.id`** (int, RESTRICT) · `idx` default 0 · **UNIQUE `(event_student_id, event_question_id)`**. — a copy of the event pivot into the attempt (order `idx`).

### 1.5 `event_student_answer`

`id` PK · `event_student_question_id` → pivot CASCADE (index) · `answer` TEXT · `is_correct` BOOLEAN default 0. — filled at submit.

### 1.6 `event_student_answer_temp` (autosave)

`id` PK · `event_student_id` → attempt CASCADE · `event_question_id` → **`event_question.id`** CASCADE · `answer` TEXT · `updated_at` default now · **UNIQUE `(event_student_id, event_question_id)`**.

> ⚠ **Key-space hazard (00 §14.3):** the value the client receives as `eventQuestionId` is **`event_student_question.id`** (the attempt pivot), but it is written to a column whose FK points at `event_question.id`. On SQLite it passes; on strict-FK Postgres autosave can fail, and `PATCH /event` (clear+re-insert) renumbers the ids so old answers become stray.

---

## 2. Flow: Event Admin (`/api/v1/event`)

All endpoints: 401 when not logged in — **no role check** (hazard 00 §6.3).

### 2.1 `GET /` (list)

`limit` 100 (1..200) · `offset ≥0` · 400 `limit_or_offset_invalid`. Filters: `category`; `published` — when present: **only `lower()=="true"` → True, anything else → False** (`published=yes` → False); `includeDisabled` truthy. `disabled=true` **never appears** (items & total). Order `eventDeadline DESC`; `includeExpired` defaults **True** (past events still show).
→ **200** `{ items: [EventOut + questionCount], total }` — `questionCount` is computed per row (**N+1**).

### 2.2 `POST /` — rate 20/minute

1. `EventCreate`:
   - `eventName` required (`eventName_required`); `eventDeadline` required (unreadable string → `eventDeadline_invalid_iso_datetime`; wrong type → `eventDeadline_invalid_datetime`);
   - `category` enum → `category_category_must_be_cub_scout_or_rover`;
   - `timeLimit` int **1..600** → `timeLimit_must_be_at_least_1` / `_at_most_600`;
   - `questionsId`: list of at least 1 item (empty → `questionsId_List_should_have_at_least_1_item_after_validation,_not_0`), non-empty string elements → `questionsId_questions_id_must_be_non_empty_strings`, unique → `questionsId_questions_id_must_be_unique`;
   - `published` bool default false; `description` optional.
2. Service (all `ValueError` → **409**):
   - resolve `question_ids` → any missing → `question_not_found: {a,b}`;
   - per question: `s.category != data.category` → `question_category_mismatch: {name}`; `s.disabled` → `question_disabled: {name}`;
   - `name = _next_name(eventName)` (slug / slug-0001…) → exhausted: `could_not_generate_unique_name`;
   - insert the event (commit), flush; insert `event_question` **in the client's `questionsId` order** (`idx = enumerate`).
3. Audit `event_created` `details={"category","n_questions"}` → commit → **201** `EventOut` + `questionCount`.

### 2.3 `GET /<name>`

Missing → 404 `event_not_found`. → **200**: `EventOut` **+ key `questions`: `[QuestionOut…]`** — only questions that resolved successfully (broken references are **silently dropped**), ordered by `idx`.

### 2.4 `PATCH /<name>` — rate 20/minute

1. `EventUpdate` (optional, `extra="ignore"`, empty → `value_no_fields_to_update`).
2. Service — ⚠ **all `ValueError` → 409, including `event_not_found`** (updating a missing event = 409, not 404):
   - `questionsId` sent (key exists):
     - empty list → `questions_id_required`;
     - resolve questions → missing → `question_not_found: …`; category (uses `data.category` when also changed, else the event's old category) → mismatch → `question_category_mismatch: {name}`; disabled → `question_disabled: {name}`;
     - **`clear_questions(name)` (bulk DELETE) + flush + re-insert** with new `idx` — the client order is kept, **`event_question` ids change**.
   - Other fields: alias map `eventName→event_name`, `timeLimit→time_limit`, `eventDeadline→event_deadline`; `category`/`published`/`description` directly → `setattr` → commit.
3. Audit `event_updated` `details.changed` → commit → re-read questions → **200** `EventOut` (**without** the `questions` array).

### 2.5 `DELETE /<name>` — rate 10/minute (**soft**)

`disabled=True; disabled_at=utcnow()` → commit → audit `event_soft_deleted` → **204**; missing → 404 `event_not_found`.

### 2.6 `POST /<name>/restore` — 10/minute → `disabled=False, disabled_at=None` → audit → **200** `{message:"restored"}`.
### 2.7 `DELETE /<name>/purge` — 5/minute (**hard**, no role check) → audit → **204**.

### 2.8 `GET /<name>/results` — login only

**No existence check** — an unknown name → **200 `{items: []}`**. The `list_results_for_event` query orders `score DESC NULLS LAST, timeLimit ASC NULLS LAST`. → `{ items: [EventStudentOut…] }` — **only `studentId`, no identity names**.

### 2.9 `EventOut` shape

`{ name, eventName, category, timeLimit, eventDeadline, published, description, disabled, disabledAt, createdAt, updatedAt, questionCount }` — **no `creatorId`** (the presenter does not expose it).

---

## 3. Flow: Student Event Attempts (`/api/v1/student/event`)

### 3.1 `GET /` (candidate list)

1. 401. `Student` missing → **200 `{items: []}`** (silent).
2. Candidates: `published = true` AND `disabled = false` AND **`eventDeadline >= now()` (DB clock)**, order `eventDeadline DESC`, **limit 500**.
3. Load all attempts of the student → `attempts_by_event`.
4. Python slice `candidates[offset : offset+limit]` (default limit 100 — **offset is applied after the 500 cap**).
5. Per item: start from `EventOut` (`questionCount=0`, **not computed**) then insert:
   - `categoryMatch = (event.category == student.category)`
   - `alreadyAttempted = attempt != null`
   - `attemptName`, `attemptScore`, `attemptCompleted = bool(attempt && finishedAt)`
6. → **200 `{ items }`** — **all categories are returned** (category filtering is via the flag only).

### 3.2 `POST /make/<event_name>` — rate 10/minute — **all guards → 409**

`make(student_id, event_name)`:
1. event missing → `event_not_found`
2. `event.disabled` → `event_disabled`
3. `not event.published` → `event_not_published`
4. `eventDeadline < now(UTC, normalized to naive)` → `event_expired`
   ⚠ naive-vs-aware comparison → `TypeError`/500 on Postgres (hazard 00 §14.4).
5. **An attempt for `(student_id, event_name)` already exists → return the old attempt as-is** (idempotent; the API still answers **201**).
6. Create `name = student-{student_id}-{event_name}-{ts}`; `startedAt = utcnow()`; flush.
7. For each `event_question` (order `idx`): insert `event_student_question(event_question_id = eq.id, idx)` — **the FK stores the `event_question` id, not the question name**.
8. Commit → audit `event_student_started` `details={"event"}` → **201** `EventStudentOut`.

**Not checked:** category match, any attempt-count limit besides the unique constraint.

### 3.3 `GET /start/<attempt_name>` — **all guards → 404**

1. attempt missing **or not owned by the student** → `attempt_not_found`
2. event missing → `event_not_found`
3. `event.disabled` → `event_disabled` — **`published`/`eventDeadline` are NOT re-checked** → a student can continue after the event has expired or been unpublished (only `disabled` blocks).
4. Resolve: map `eq.id → eq`; for each `esq` pivot, take `eqs[esq.event_question_id].question_id` when present.
5. Fetch `answer_temp` as `savedAnswers`.
6. **200**:
```json
{"event": EventOut, "eventStudent": EventStudentOut,
 "questions": [{"eventQuestionId": <event_student_question id>, "question": QuestionOut}],
 "savedAnswers": [{"eventQuestionId": <temp value>, "answer": "..."}]}
```
Questions that fail to resolve are **skipped** from the list. `QuestionOut.description` (optional) is rendered muted above the prompt in the runner.

### 3.4 `POST /answer-temp` — rate 120/minute → guards **404**

Same model validator as practice (`value_must_specify_practice_or_event_student` / `_question_id`); empty pair → 400 `event_student_name_and_event_question_id_required`.
`save_temp(student_id, attempt, event_question_id, answer)`:
- attempt missing/wrong owner → `attempt_not_found`
- already submitted → `attempt_already_submitted` (**404**, not 409)
- event disabled → `event_disabled`
- upsert on UNIQUE `(event_student_id, event_question_id)` → commit → **200** `{ notEmpty }`. **Not checked** whether `event_question_id` belongs to the attempt's event.

### 3.5 `POST /store` — rate 10/minute → guards **409**

1. `SubmitAnswers` → 400 `value_must_specify_practice_or_event_student` / `value_answers_required`; empty `eventStudentName` → 400 `event_student_name_required`.
2. `submit(student_id, attempt_name, answers)`:
   - missing/wrong owner → `attempt_not_found`; already submitted → `attempt_already_submitted`; event disabled → `event_disabled` (all **409**).
   - `answer_map = { int(a.event_question_id): a.answer }` — ⚠ an element without `eventQuestionId` → `int(None)` → **500** (hazard 00 §14.3).
3. Scoring — iterate the pivots `esqs` (order `idx, id`):
   - `eq = eqs.get(esq.event_question_id)` → missing → **`continue`**;
   - `question = get_by_name(eq.question_id)` → missing → **`continue`**;
   - `answer = answer_map.get(esq.id)` (**key = pivot id**);
   - `correct = _is_correct(question, answer)` (spec 03 §6) → insert `event_student_answer(event_student_question_id=esq.id, answer, is_correct)`; `if correct: score += 10`.
4. Set `attempt.score`, `finishedAt = utcnow()`, `timeLimit = int(seconds)` when `startedAt` → commit.
5. **No** enforcement of `timeLimit`/`eventDeadline`/`published` at submit (hazard 00 §14.9).
6. Audit `event_student_submitted` `details={"score"}` → **200** `EventStudentOut`.

---

## 4. Attempt Status Contract

| Condition | Representation |
|---|---|
| Never participated | no attempt → `alreadyAttempted=false` |
| In progress | attempt exists, `finishedAt = null` → UI badge "In Progress", **Continue** button |
| Completed | `finishedAt` filled + `score` → badge "Completed", **View Result** button |
| Time limit | **frontend only** (`startedAt + timeLimit×60s`); the backend does not terminate an attempt |

---

## 5. Error Catalog

| Code | message |
|------|---------|
| 400 | `eventName_required`, `eventDeadline_required`, `eventDeadline_invalid_iso_datetime`, `eventDeadline_invalid_datetime`, `category_category_must_be_…`, `questionsId_questions_id_must_be_unique`, `questionsId_questions_id_must_be_non_empty_strings`, `questionsId_List_should_have_at_least_1_item_after_validation,_not_0`, `timeLimit_must_be_at_least_1`, `timeLimit_must_be_at_most_600`, `value_no_fields_to_update`, `event_student_name_required`, `event_student_name_and_event_question_id_required`, `limit_or_offset_invalid` |
| 401 | `unauthorized` |
| 404 | `event_not_found` (GET/PATCH? **PATCH → 409**), soft-delete/restore/purge `event_not_found`; attempt: `attempt_not_found`, `event_not_found`, `event_disabled`; answer-temp: `attempt_not_found`, `attempt_already_submitted`, `event_disabled` |
| 409 | create: `question_not_found: {names,comma-separated}`, `question_category_mismatch: {name}`, `question_disabled: {name}`, `could_not_generate_unique_name`; **update: everything including `event_not_found`**, `questions_id_required`, `question_*`; make: `event_not_found`, `event_disabled`, `event_not_published`, `event_expired`; store: `attempt_not_found`, `attempt_already_submitted`, `event_disabled` |
| 429 | `rate_limit_exceeded` |

---

## 6. UI Flow (Vue)

### 6.1 Admin list — `/event` (`event`)

- Header: **Open Student** → `event-student`; **Create Event** → `event-new`.
- Filters: search (client-side `eventName`); category & published (**server-side**, no debounce): `published 'true'→true / 'false'→false / ''→absent`.
- Columns: Name · Category (badge) · Duration (`timeLimit`) · Deadline (`eventDeadline` id-ID) · Status (**`Published` green / `Draft` gray** + small text `{questionCount} questions`) · Actions.
- Row actions: **Play** (only `v-if="canStart"` = `!!auth.student`) → `POST /student/event/make/{name}` → toast → `/student/event/start/{attempt.name}`; **Edit** → the form. **No delete** in the list.
- Footer when `!canStart`: *"The Start button is hidden because the current account has no student row. Log in as a student (/student-login) to test an event as a student."*

### 6.2 Admin form — `/event/new`, `/event/:name/edit`

- Fields: Event Name (required); Category; **Duration (minutes)** number `min=1 max=600` default 60; **Event Deadline** `datetime-local` required; Description; a scrollable **Select Questions** box (`max-h-64`, a checkbox per question); **Publish** checkbox default false.
- **Selection logic**: `filteredQuestions = allQuestions.filter(q => q.category === form.category && q.status === 'Active')` — changing the category changes the option list; label `Select Questions ({n} available)`; `allQuestions` = `listQuestions({limit:200})`.
- Edit load: `eventDeadline` truncated `.slice(0,16)`; `questionsId = ev.questions.map(q => q.name)`.
- Payload: `{eventName, category, timeLimit, eventDeadline: new Date(...).toISOString(), description?, published, questionsId}` → create `POST` / edit `PATCH` → redirect to detail; on failure → inline `error`.

### 6.3 Admin detail — `/event/:name`

`GET /event/{name}`. Heading; sub `{CATEGORY} • {n} minutes • Deadline: {id-ID}`; optional description; a **Questions ({n})** list in order (`<ol>`); links **Edit**, **View Results** (`/event/{name}/results`), **Back**.

### 6.4 Admin results — `/event/:name/results`

Load `GET /event/{name}/results`. States: "Loading…" / **"No student has submitted yet."** / a table `# · Student (raw `studentId` shown) · Score (score ?? '—') · Duration ({timeLimit}s) · Submit Time`.

### 6.5 Student list — `/student/event` (`event-student`)

- Breadcrumb Dashboard → Events; header **"Your category: {session.studentCategory}"**.
- Search + category filters = **client-side**. Load `GET /student/event`; 6 skeletons / error+Retry / empty (*"Bebras challenge events will appear here when available."*).
- A grid of `EventCard` with handlers: `onStart` → make → toast → `/student/event/start/{attempt.name}` (per-card spinner via `starting`); `onContinue` → `/student/event/start/{attemptName}`; `onViewResult` → `/student/event/result/{attemptName}`; `onViewDetail` → `/student/event/start/{event.name}?preview=1` ⚠ **dead path** (the endpoint expects an attempt name, the `preview` param is ignored → "Attempt not found").

### 6.6 Card — `EventCard` (exact branches)

- Gradient header: cub emerald / scout blue / rover purple / fallback gray.
- Top-right badge: `alreadyAttempted && attemptCompleted` → **"Completed" green**; `else if alreadyAttempted` → **"In Progress" orange**. Top-left: `!categoryMatch` → **"Category mismatch" red**. Category badge: blue when matched else gray.
- Meta: `{timeLimit} minutes` · `Deadline {id-ID}` · `{questionCount} questions` · description max 2 lines.
- Score footer: only when completed → `Score: {attemptScore ?? '—'}`.
- Buttons (exclusive): **(1)** completed → outline **"View Result"** · **(2)** in progress → solid **"Continue"** · **(3)** not attempted → solid **"Start"** with `:disabled="!event.categoryMatch"` · **(4)** ghost preview **only when `!categoryMatch`**.

### 6.7 Student runner — `/student/event/start/:name` (`event-student-start`)

- Param = **the attempt name**. Mount → `GET /student/event/start/{name}`; on failure → "Attempt not found."
- Header: `event.eventName`; "Question {i+1} of {n}"; while active "• Answers are saved automatically".
- **Countdown**: `durationMin = event.timeLimit ?? 0` (0 → no countdown); `deadline = startedAt + durationMin×60.000`; red chip "Time's up!"; amber ≤60s; gray; **auto-submit when expired**.
- Questions: `v-html` question; MC → radio a..d rendered as rich HTML (blue highlight, image-only options render, images capped at 192px via `max-h-48`, empty option `(empty)` in italics); Essay → `textarea rows=6`.
- Answers: `setAnswer` → local + `POST /student/event/answer-temp` fire-and-forget.
- Footer: **Previous** / pager (active blue, answered green, unanswered gray) / **Next** blue or **Submit Answers** green (`:loading`).
- **Submit**: all `{eventQuestionId, answer}` (null when empty) → `POST /student/event/store` → `Object.assign(eventStudent, attempt)` → `/student/event/result/{name}`; on failure → toast "Failed to submit the event".
- **Leave guard** active: `dialog.confirm` "Leave Event?" — *"…Answers already filled in will be saved and graded automatically. Are you sure you want to leave?"* → **"Keep Working"** / **"Save & Leave"** (submit → toast "Event graded" → redirect to result; on failure → cancel navigation); + `beforeunload`.

### 6.8 Student result — `/student/event/result/:name`

`fetchJson GET /student/event/{name}` (errors swallowed). "Your score" → `{{ attempt.score ?? 0 }}` large green; "Duration: {n} seconds"/"—". PageHeader right actions (shown once `attempt` loads): **Back to event list** (solid) + **Dashboard** (outline) buttons. The shared **`CelebrationOverlay`** auto-plays once per session for a finished attempt (`attempt.finishedAt` set — an in-progress attempt opens the page without it; `onceKey={event:{attemptName}}` — see spec 03 §9.3): balloons popping into confetti + `celebration.title` headline; skipped under `prefers-reduced-motion` beyond a short headline fade.

### 6.9 Access

Admin event routes have `meta.role:'admin'` (not enforced); student routes have `meta.role:'student'` (also not enforced) — a student can open `/event`, staff can open `/student/event`; the backend **only checks login**.
