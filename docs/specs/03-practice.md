# 03 — Practice (Student Practice Sheet)

> Parent: [`00-master-overview.md`](00-master-overview.md)
> Scope: `practice` + 4 child tables, API `/api/v1/student/practice` (student) + `staff_bp` `/api/v1/practice` (staff), the practice runner frontend, the admin before/after-shuffle detail.

---

## 1. Entity & Tables

### 1.1 `practice`

| Column | Type | Notes |
|-------|------|-------|
| `name` | VARCHAR(140) PK | `student-{student_id}-{unix_timestamp}` — **no uniqueness check** |
| `student_id` | INTEGER NOT NULL → `ab_user.id` CASCADE | index |
| `category` | VARCHAR(20) NOT NULL default `'cub'` | **snapshotted from `student.category` at create** (index) |
| `score` | INTEGER nullable | 0..100, filled at submit |
| `timeLimit` | INTEGER nullable | seconds, filled at submit |
| `startedAt` | DATETIME nullable | filled at create |
| `finishedAt` | DATETIME nullable | filled at submit — **the terminal-state marker** |
| `created_at`, `updated_at` | DATETIME default now | |

### 1.2 `practice_before_shuffle`

`id` PK · `practice_id` → `practice.name` CASCADE (index) · `question_id` → `question.name` RESTRICT · `original_idx` INTEGER default 0. — question order **before** the shuffle (pool order).

### 1.3 `practice_question`

`id` PK · `practice_id` CASCADE · `question_id` RESTRICT · `shuffled_idx` INTEGER default 0 · **UNIQUE `(practice_id, question_id)`** · index `(practice_id, shuffled_idx)`. — display order (after the shuffle).

### 1.4 `practice_answer`

`id` PK · `practice_id` CASCADE · `question_id` RESTRICT · `answer` TEXT · `is_correct` BOOLEAN default 0 · **UNIQUE `(practice_id, question_id)`**. — filled at submit.

### 1.5 `practice_answer_temp`

`id` PK · `practice_id` CASCADE · `question_id` RESTRICT · `answer` TEXT · `updated_at` default now · **UNIQUE `(practice_id, question_id)`**. — autosave; upserted per answer.

---

## 2. Flow: Create (`POST /create`) — rate 10/minute

`PracticeService.create(student_id)` — sheet size `minQuestions` comes from the settings key **`practiceMinQuestions`** (fail-safe default **10**, see §10):

1. `Student` missing → `ValueError("student_not_found")` → API **409**.
2. Fetch the pool: `question_repo.list_all(category=student.category, status="Active", limit=500)` — order `created_at DESC`, **`disabled` automatically excluded**.
3. `len(pool) < minQuestions` → `ValueError(f"insufficient_question_in_category: have {len(pool)}, need {minQuestions}")` → **409** (dynamic message).
4. `picks = random.sample(pool, minQuestions)` — N random questions without replacement.
5. `name = f"student-{student_id}-{int(datetime.utcnow().timestamp())}"`; insert `Practice(name, student_id, category=student.category, startedAt=utcnow())` + flush.
6. **Shuffle recording:**
   - `original_picks = [s for s in pool if s in picks]` → the **before-shuffle** order = the pool order (`created_at DESC`) intersected with the selected questions;
   - `shuffled_picks = list(picks); random.shuffle(shuffled_picks)`;
   - insert `before_shuffle` per `original_picks` (`original_idx` = 0..N-1);
   - insert `practice_question` per `shuffled_picks` (`shuffled_idx` = 0..N-1).
7. commit (service) → API: audit `practice_created` `details={"category"}` → commit → **201** `PracticeOut`.

> Porting note: the first assignment `original_picks = original_order[:SHEET_SIZE]` is immediately overwritten (dead code). The `timeLimit` column is **never filled at create** — there is no backend time limit for practice.

---

## 3. Flow: Resume (`GET /start`) — default rate

1. `list_for_student(student_id, limit=1)` → the latest practice (`created_at DESC`).
2. None, **or `finishedAt is not None`** → service `None` → API **404** `{message:"no_active_practice"}`.
3. **200**:
```json
{"practice": PracticeOut,
 "questions": [{"questionId": "<question.name>", "question": QuestionOut|null}],
 "savedAnswers": [{"questionId": "<question.name>", "answer": "..."}]}
```
`questions` is ordered by `shuffled_idx`; `savedAnswers` = all `answer_temp` rows of the practice. `QuestionOut.description` (optional) is rendered muted above the prompt in the runner.

---

## 4. Flow: Autosave (`POST /answer-temp`) — rate **120/minute**

1. `AnswerTemp` Pydantic — model validator: without `practiceName` **and** `eventStudentName` → 400 `value_must_specify_practice_or_event_student`; with `practiceName` but without `questionId` → 400 `value_must_specify_question_id`.
2. Defensive guard: empty pair → 400 `practice_name_and_question_id_required`.
3. `save_temp(student_id, practice_name, question_id, answer)`:
   - practice missing **or not owned by the student** → `ValueError("practice_not_found")` → **404** (an ownership failure cannot be distinguished from not-found);
   - `finishedAt is not None` → `ValueError("practice_already_submitted")` → **404** (not 409 — see hazard 00 §14.5);
   - **upsert** the temp row on UNIQUE `(practice_id, question_id)` → commit.
4. → **200** `{ notEmpty: bool(answer) }`. No audit.

---

## 5. Flow: Submit & Score (`POST /store`) — rate 10/minute

1. `SubmitAnswers` — model validator: without a target → 400 `value_must_specify_practice_or_event_student`; without `answers` → 400 `value_answers_required`. Guard: empty `practiceName` → 400 `practice_name_required`.
2. `submit(student_id, practice_name, answers)` — `ValueError` → **409**:
   - missing / not owned → `practice_not_found`
   - already submitted → `practice_already_submitted`
3. Build `answer_map = { a["question_id"]: a["answer"] }` from the payload (key = `questionId`; the answers list is a raw dict list — a mismatched key is not caught by validation → KeyError 500 / `None` never matches).
4. Iterate `get_questions` (order `shuffled_idx`):
   - `question = get_by_name(q.question_id)`; **`question is None → continue`** (no answer row, no points);
   - `correct = _is_correct(question, answer_map.get(q.question_id))` (§6);
   - insert `PracticeAnswer(practice_id, question_id, answer, is_correct)`;
   - `if correct: score += 10`.
5. Set `practice.score = score`; `finishedAt = utcnow()`; `timeLimit = int((finished − startedAt).total_seconds())` **only when `startedAt` is filled**; commit.
6. Audit `practice_submitted` `details={"score"}` → commit → **200** `PracticeOut`.

**No** time-limit enforcement, no submit-count limit after the terminal state, and no `category` re-validation.

---

## 6. Scoring Engine (shared with event)

```
_is_correct(question, answer):
    if answer is empty / whitespace only  → False
    j = trim(lower(answer))
    if questionType == "Multiple Choice" → bool(correctAnswer) and j == lower(correctAnswer)
    else (Essay)                          → False          # no auto-grade
```

`score = 10 × correct count` (constants `POINTS_PER_CORRECT=10`, `SHEET_SIZE=10` → 0..100). Essay always contributes 0 points.

---

## 7. Flow: Detail

### 7.1 `GET /<name>` — dispatch by role

```python
role = app_role or ("admin" if a FAB role "Admin" exists else "user")
is_staff = role in {admin, moderator, course_creator}
```
- **Staff** → admin payload (§7.2).
- **Student** → `detail_payload(name, student_id=current_user.id)`; missing / not owned → 404 `practice_not_found`.

**Student 200 payload:**
```json
{"practice": PracticeOut,
 "questions": [{"questionId", "question": QuestionOut|null}],
 "answers":   [{"question_id", "answer", "isCorrect"}],
 "beforeShuffle": [{"questionId", "question": QuestionOut|null, "originalIdx"}]}
```
(No `afterShuffle` — `questions` is already in display order.)

### 7.2 `GET /admin/<name>` (alias of `GET /<name>` for staff)

`admin_detail_payload` → missing → 404 `practice_not_found`. **200:**
```json
{"practice": PracticeOut, "student": StudentOut|null,
 "beforeShuffle": [{"questionId","question","originalIdx"}],
 "afterShuffle":  [{"questionId","question","shuffledIdx"}],
 "answers":       [{"question_id","answer","isCorrect"}]}
```
⚠ The `answers` key uses **snake_case** (`question_id`) unlike the other lists (camelCase).

### 7.3 `GET /mine` → `{ items: [PracticeOut…] }`, order `created_at DESC`, service limit 100 (no API clamp).

### 7.4 `GET /` (admin list) — login only, no role check

`limit` 100 (1..200) · `offset ≥0` · 400 `limit_or_offset_invalid`. Filter `category`; `student_id` **only when it is all digits** (otherwise silently ignored). → paginated `{ items, total, page, perPage }`. Items = **`PracticeAdminOut`** = `PracticeOut` + `studentName: str|null` (display name `"{firstName} {lastName}"` joined from `users` in one batch query) + `studentEmail: str|null` (`users.email`, `null` when empty) + `studentSchool: str|null` (`students.school`, `null` when empty). All three keys are absent from the JSON when no student row resolves (or the value is empty), so the UI falls back to a short `studentId`.

---

## 8. Error Catalog

| Code | message |
|------|---------|
| 400 | `value_must_specify_practice_or_event_student`, `value_must_specify_question_id`, `value_answers_required`, `practice_name_and_question_id_required`, `practice_name_required`, `limit_or_offset_invalid` |
| 401 | `unauthorized` |
| 404 | `no_active_practice` (empty resume) · `practice_not_found` (save_temp: missing/wrong owner) · `practice_already_submitted` (save_temp after submit) · `practice_not_found` (detail) |
| 409 | `student_not_found` (create) · `insufficient_question_in_category: have {n}, need {minQuestions}` · `practice_not_found` (store: wrong owner) · `practice_already_submitted` (store) |
| 429 | `rate_limit_exceeded` |

---

## 9. UI Flow (Vue)

### 9.1 List (student) — `/student/practice` (`practice`)

- Breadcrumb: Dashboard (`student-dashboard`) → Practice.
- Header action **Start Practice** (`:loading="starting"`) → `POST /student/practice/create` → toast "A new practice sheet was created" → `router.push('/student/practice/start')`; on failure → error toast. (No `auth.student` guard on this page.)
- Load `GET /student/practice/mine`; states: 6 skeletons / error+Retry / empty (box + a "Start Practice" button) / a grid of `PracticeCard`.
- `PracticeCard` (the whole card links to `practice-detail`): gradient per category (cub emerald / scout blue / rover purple); a **`Completed` green** badge when `finishedAt`, a **`Not Submitted` orange** badge when `startedAt`, else none; title `Practice {createdAt id-ID}`; a `Score {score}` row or **"Not graded"**; a duration label: when started+finished → `Duration {n} minutes|hours` (timestamp difference, rounded, min 0); else when `timeLimit` → `Limit {n} minutes`; else `—`.

### 9.2 Runner — `/student/practice/start` (`practice-start`, no param)

1. Mount → `GET /student/practice/start`; on failure → `payload=null` → "There is no practice in progress. Start a new practice from the practice list."
2. **Countdown**: `durationMin = practice.timeLimit ?? 30` (the default constant `DEFAULT_PRACTICE_DURATION_MIN = 30`; `0` → no deadline); `deadline = (startedAt || now) + durationMin×60.000`. Chip: expired → red bg + "Time's up!"; `timeLeft ≤ 60s` → amber; else gray. `useCountdown(deadline, onExpire → auto submit)`.
3. Questions: `v-html` question; MC → radio a..d from `optionA..D` rendered as rich HTML (blue highlight when selected, image-only options render, images capped at 192px via `max-h-48`, empty option `(empty)` in italics); Essay → `textarea rows=6`.
4. **Answer**: `setAnswer(value)` → store locally `answers[questionId]` + `POST /student/practice/answer-temp` **fire-and-forget** (`.catch(()=>{})`, silent failure).
5. Footer: **Previous** disabled at index 0; numeric pager — current `bg blue`, answered `bg green`, unanswered `bg gray`; on the right **Next** (blue) while `index < len-1`, otherwise **Submit Answers** (green, `:loading="submitting"`).
6. **Submit**: send all `{questionId, answer}` (null when empty) → `POST /student/practice/store` → set `practice.finishedAt` locally → `submitted=true` → `router.push('/student/practice/{name}')`; on failure → toast "Failed to submit the practice".
7. **Leave guard** (`onBeforeRouteLeave`, while `isActive`): `dialog.confirm` "Leave Practice?" — *"You are working on a practice. Answers already filled in will be saved and graded automatically. Are you sure you want to leave?"* → actions **"Keep Working"** (cancel) / **"Save & Leave"** (submit → toast "Practice graded" → navigate to `practice-detail`; on failure → navigation is cancelled). + `beforeunload` while active.
8. `savedAnswers` from the response re-populates the answer map.

### 9.3 Result (student) — `/student/practice/:name` (`practice-detail`)

Load `GET /student/practice/{name}` (role dispatch). Header "Practice"; PageHeader right action (once loaded): **Back to practice list** (outline) button. Sub `Category: {label} • Finished: {formatDate}`. A **Score** card = `score ?? 0` (large green). **Answer Detail**: an `<ol>` per question — `question.description` muted above the rich HTML question (images capped at 192px, both sanitized), falling back to "This question is unavailable." when the question was purged; the answer row color from `answers[].isCorrect` (green `✓` / red `✗`); unanswered → `(not answered)`; the letter is displayed uppercase. When the page appears for a submitted practice (`practice.finishedAt` set — an attempt still in progress opens the page without the overlay), the shared **`CelebrationOverlay`** auto-plays once — rising balloons that pop into confetti + a `celebration.title` headline ("Selamat!"); `onceKey={practice:{name}}` in `sessionStorage` prevents replays on refresh, the overlay is `pointer-events-none`, and `prefers-reduced-motion` shows only the headline.

### 9.4 List (admin) — `/practice` (`practice-admin`)

- Header actions: **Open Student** → `StudentList`; **Settings** → opens the *Practice settings* dialog (see §10).
- `GET /api/v1/practice` (category filter via Select `All | Cub | Scout | Rover`). Columns: Student — two-line cell: `studentName` on top (falling back to a short `studentId` when the student row is gone) with `studentEmail` as the `text-p-xs` sub-line when present; School (`studentSchool ?? '—'`, hidden below `md`); Category (blue badge), Score (`score ?? '—'`), Date (`createdAt` locale), Status (`Completed` / `In Progress` badge). Row → `practice-admin-detail`.
- Settings dialog (`size="sm"`, fetched on open from `GET /api/v1/practice/settings`, skeleton while loading): **admin** → `FormControl type=number :min=1` "Questions per practice" + **Save** (`PUT /practice/settings`, client validation → toast error on invalid value, toast success + close); **non-admin staff** → read-only value card with *"Only admins can change this."* Action list = Cancel, plus Save only when `auth.isAdmin`. Fetch/API errors → `ErrorMessage` in dialog / `toast.error`.

### 9.5 Detail (admin) — `/practice/:name`

Load `GET /api/v1/practice/{name}`. Sub when `data.student`: `Student: {firstName lastName} ({CATEGORY})` + a Score / `In Progress` badge, plus a `text-p-xs` sub-line `email • school` (whichever is present, joined with `•`). Sub when the student row is gone: `Student: {short studentId}` + the same Score / `In Progress` badge (shown in both branches). Two columns: **Before Shuffle** (`beforeShuffle`) vs **After Shuffle** (`afterShuffle`) — both render `question.description` muted above a divider, the rich HTML `question.question`, and MC options via `QuestionOptions` (rich HTML, image-only supported, images capped at 192px). An **Answers** list: per question the same description/question/`QuestionOptions` (with selected + correct marks), fallback raw `answer` when the answer is not an a–d letter, green/red color from `isCorrect`, empty → `(not answered)`. No action navigation.

## 10. Settings (min questions)

Sheet size is configurable at runtime through the shared `settings` table (key/value, see 06) — key **`practiceMinQuestions`**, fail-safe default **10** when unset/invalid/non-positive (helper `app/infra/settings.py`, read fresh on every create).

| Endpoint | Gate | Behavior |
|---|---|---|
| `GET /api/v1/practice/settings` | `require_staff` | `{"minQuestions": <int>}` |
| `PUT /api/v1/practice/settings` | `require_role("admin")` | body `{"minQuestions": ≥ 1}` (400 otherwise) → upsert + audit `practice_settings_updated`; idempotent (unchanged value → no write, no audit) |

`create()` reads the key for both gates: the pool check (`have {n}, need {minQuestions}` → 409) and `random.sample(pool, minQuestions)` — so the 409 message always shows the live value.

**UI:** *Practice settings* dialog on the admin list page `/practice` (§9.4) — header button **Settings**; staff (non-admin) get a read-only view, admins can edit.
