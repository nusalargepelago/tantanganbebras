# Master Overview — Tantangan Bebras Feature Specification

> **Document purpose:** cross-feature technical specification of Tantangan Bebras as a reference for re-implementation onto another stack. This document is the parent of [`01-auth-student-users.md`](01-auth-student-users.md), [`02-topic-question.md`](02-topic-question.md), [`03-practice.md`](03-practice.md), [`04-event.md`](04-event.md), [`05-student.md`](05-student.md), [`06-supporting.md`](06-supporting.md), [`07-seeder-default-pack.md`](07-seeder-default-pack.md).
>
> **Reference sources:** production code `backend/app/` (64 files), `frontend/src/`, migration schema `0001–0012`, seeder `scripts/seed_demo.py`.

---

## 1. System Architecture

```
Vue 3 SPA (Frappe UI)
  ↓  fetch + session cookie + X-CSRFToken header
API (Flask-AppBuilder Blueprint, app/api/*.py)   — manual auth guard, rate limit, audit commit
  ↓  request body
DTO (Pydantic v2, app/dto/*.py)                  — validation + formatted error messages
  ↓  model_dump(by_alias=True)
Service (app/services/*.py)                      — business logic, ValueError → status code
  ↓
Repository (app/repositories/*.py)               — query, filter, ordering; never commits
  ↓
Model (SQLAlchemy 2.0, app/models/*.py) → SQLite/PostgreSQL (Alembic 0001–0012)

Cross-cutting: Flask-Login (session) · Flask-Limiter · Flask-Talisman · CSRF · AuditLog (flush)
```

**Reference stack:** Backend — Flask + Flask-AppBuilder 5, SQLAlchemy 2.0, Alembic, Pydantic v2, Flask-Login, Flask-Limiter (memory, fixed-window), Flask-Talisman, Waitress (prod). Frontend — Vue 3 + Vite + TypeScript + Pinia + Vue Router 4 + frappe-ui + Tailwind. Port app: backend 8080, Vite dev 5173.

**Layering rules:** the API calls services for business logic; some read endpoints call repositories directly (e.g. `GET /event/:name` → `QuestionRepository.get_many_by_names`); services do not know HTTP; repositories never commit (commit happens in the service or in the API after audit); presenters (`app/presenters/*.py`) are the single place for the wire format (camelCase).

---

## 2. Cross-cutting Conventions

| Aspect | Convention |
|-------|----------|
| Auth | Session cookie Flask-Login; **every endpoint** starts with a manual guard `current_user.is_authenticated` → `401 {"message":"unauthorized"}`. FAB `@expose` does not check permissions. |
| RBAC | Reads `UserProfile.app_role` (`admin`/`moderator`/`course_creator`/`user`) via `require_role` / `require_owner_or_role` / `_is_admin()`. **FAB role names (`Admin`, `Moderator`, …) are separate** — there is no automatic bridge. |
| Primary key | Natural string `name VARCHAR(140)` (slug) for `question`, `topic`, `event`, `event_student`, `practice`; autoincrement int for pivot/answer/audit/todos; `student.user_id` = PK = FK to `ab_user.id`. |
| Soft delete | Columns `disabled BOOLEAN` + `disabled_at DATETIME` + index — only `question`, `event`, `student`. `topic` & `todos` = hard delete. Restore = `disabled=False, disabled_at=None`. |
| Audit | Table `audit_logs`; `services/audit.py::log()` only **flushes** → **the caller must `db.session.commit()`**. Failure is swallowed + the flush is rolled back. IP = first `X-Forwarded-For` hop (max 45 chars) or `remote_addr`. |
| Timestamp | All `created_at`/`updated_at`/`time_*` naive UTC (`datetime.utcnow()`, `server_default=now`). |
| Wire format | Success is **flat** (no envelope): `{"items":[…],"total":n}` or the object directly. Fields are **camelCase** via `model_dump(by_alias=True)`. Errors are always `{"message":"<string>"}`. |
| Timestamp on wire | Tantangan Bebras presenters use `_iso_utc()` → naive treated as UTC, output `…+00:00`. `UserOut`/`TodoOut` use plain `isoformat()` (no timezone) — **inconsistent, decide at port time**. |
| Pagination | `limit`/`offset` must be int → `400 limit_or_offset_invalid`. Clamp: default 100 (1..200); topic default 200 (1..500); todos (1..500). Some lists have no `total`. |
| Rate limit | Default **60/minute** on all routes; key `user:<id>` / `ip:<addr>`; in-memory per-process storage; `429 {"message":"rate_limit_exceeded"}` + `X-RateLimit-*` headers. Per-route overrides in §7. |
| CSRF | Header `X-CSRFToken` / `X-Csrf-Token` for all non-GET `/api/*`; active only when `CSRF_ENABLED=true` **and** `DEBUG=false`. `400 missing_csrf_token` / `invalid_csrf_token`. |
| Service errors | `ValueError("<code>")` raised by services → the API maps it to a status (table in each domain spec; **inconsistent — 404/409/413 depends on the endpoint**). |
| DTO validation | Only the **first** error is shown: `"{field}_{message}"` — formatter in §10. |
| Upload | `app/static/uploads/`, random name `secrets.token_hex(16).ext`, served via `GET /uploads/<path>`. |
| Scoring | 10 points per correct MC answer (`POINTS_PER_CORRECT=10`), 10-question sheet (`SHEET_SIZE=10`) → score 0..100. Essay is not auto-graded. |
| Ordering | Default list: question `created_at DESC`; topic `category, idx, name`; student `created_at DESC`; event `eventDeadline DESC`; practice/attempt `created_at DESC`; event results `score DESC NULLS LAST, timeLimit ASC NULLS LAST`. |

---

## 3. Entity Relationship

```
ab_user (FAB) ──┬── user_profile        1:1 (user_id UNIQUE) — full_name, app_role, subscription_*
                  ├── ab_user_role ── ab_role (Admin | Moderator | Course Creator | Tantangan Bebras Student | Batch Evaluator)
                  ├── student           PK user_id — category, school, city, country, status, disabled
                  ├── todos               creator_id CASCADE
                  ├── audit_logs          user_id SET NULL (audit survives user deletion)
                  ├── topic           creator_id — title, category, idx
                  ├── question        creator_id, topic_id→topic.name SET NULL
                  ├── event           creator_id — eventName, category, timeLimit, eventDeadline, published, disabled
                  ├── event_student     student_id CASCADE, event_id→event.name — UNIQUE(student_id,event_id)
                  └── practice         student_id CASCADE — category, score, startedAt/finishedAt

topic.name ◄──── question.topic_id (SET NULL)

event ──< event_question (event_id CASCADE, question_id→question.name RESTRICT, idx, UNIQUE(event,question))
                   │
event_student ──< event_student_question (event_student_id CASCADE, event_question_id→event_question.id, idx, UNIQUE)
                         ├──< event_student_answer        (event_student_question_id CASCADE, answer, is_correct)
                         └──< event_student_answer_temp   (event_student_id CASCADE, event_question_id, answer, UNIQUE(student,question))

practice ──┬── practice_before_shuffle (question_id→question.name, original_idx)
               ├── practice_question        (question_id, shuffled_idx, UNIQUE(practice,question))
               ├── practice_answer          (question_id, answer, is_correct, UNIQUE(practice,question))
               └── practice_answer_temp     (question_id, answer, UNIQUE(practice,question))
```

**15 application tables** + 13 FAB security tables (`ab_*`) + `alembic_version`. Full column fields: see §1.1–1.n in each domain spec.

**Key relations:**
- `student` = **discriminator** row for a student above `ab_user` (its existence = student account). Its soft delete also sets `ab_user.active`.
- `event_question.id` (int) vs `question.name` (string) — the attempt stores **pivot ids**, not question names.
- Practice question order is kept twice: `before_shuffle` (pool order) + `question.shuffled_idx` (display order).

---

## 4. State Machines

| Domain | Entity | State |
|--------|--------|-------|
| Question bank | `question` | lifecycle: **active → (DELETE) disabled → (restore) active → (purge) gone**; separate field `status: Active ↔ Inactive` (availability filter) |
| Event | `event` | lifecycle: **active → disabled → restore → purge**; field `published: false ↔ true` (PATCH); expired = `eventDeadline < now` (derived, not stored) |
| Student | `student` | `status: Inactive → Active` (activate; self-register always starts `Inactive`); lifecycle soft delete **disabled + `ab_user.active=False`** → restore → purge (hard) |
| Practice | `practice` | **created (startedAt) → submitted (finishedAt + score)**; terminal — cannot be re-answered; resume = only the latest unsubmitted practice |
| Event attempt | `event_student` | **created (startedAt) → submitted (finishedAt + score)**; terminal; **idempotent**: re-`make` returns the old attempt; one per `(student_id, event_id)` |
| Autosave | `*_answer_temp` | permanent upsert; new rows are created only before submit (submit does not delete temp) |
| User | `ab_user.active` | register/create = `True`; student soft delete = `False`; staff login **does not check** `active`, student login does |

Transition guards (exact error messages) are in each domain spec.

---

## 5. Naming & Sequences

`_slugify(v)`: `strip().lower()` → replace non-`[a-z0-9]` with `-` → strip `-` → truncate to 80 chars → fallback when empty.

| Entity | `name` algorithm | Unique? | Exhaustion |
|--------|------------------|-------|------------|
| `topic` | `slug(title)`; conflict → `slug-0001`…`slug-0999` | yes (DB check loop) | 409 `could_not_generate_unique_name` |
| `question` | `slug(questionCode or "Mini Challenge")`; conflict → `slug-{year}-0001`…`-0999` | yes | 409 `could_not_generate_unique_name` |
| `event` | `slug(eventName)`; conflict → `slug-0001`… | yes | 409 `could_not_generate_unique_name` |
| `practice` | `student-{student_id}-{unix_ts}` | **not checked** | same-second collision → PK violation (hazard) |
| `event_student` | `student-{student_id}-{event_name}-{unix_ts}` | **not checked** | same |
| Student username | input as-is (self) / = email (admin & staff register) | unique in `ab_user` | 409 |
| Upload file | `secrets.token_hex(16).{ext}` | random | — |

There is no document numbering with sequences (no `INV-…`); the only numbering is the slug uniqueness suffix.

---

## 6. Auth & RBAC

### 6.1 Two login paths

| | Staff | Student |
|---|---|---|
| Endpoint | `POST /api/v1/auth/login` | `POST /api/v1/student/auth/login` |
| Identifier | `email` (`@` in username → lookup by email) | `username` |
| Check `active` | **no** | yes |
| Check student `disabled` | — | yes → 401 |
| Role | any FAB role / no role | required `Tantangan Bebras Student` (created at register) |
| Default `app_role` | `user` (register) / — | `user` |

### 6.2 Authorization helpers (`app/utils/auth.py`)

| Helper | Rule | Response |
|--------|--------|----------|
| `require_role(api, *roles)` | 401 if not logged in; 403 if `app_role` mismatch | 401 `unauthorized` / 403 `forbidden` |
| `require_owner_or_role(api, owner_id, *roles)` | allowed if `current_user.id == owner_id` **or** `app_role` matches | 401 / 403 `forbidden` |
| `_is_admin()` (user_admin.py) | `app_role ∈ {admin, moderator, course_creator}` | 403 `forbidden` |

### 6.3 Actual enforcement per endpoint (ground truth)

| Group | Gate |
|----------|------|
| `todos` get/update/delete | `require_owner_or_role(…, "admin")` |
| `users` list/create/get/update/delete | `_is_admin()` ( **`/role-list` is not checked** ) |
| `topic`, `question` mutations | `_author_or_mod()` — **always returns None (never rejects)** |
| `event`, `student/event`, `student/practice`, `student` CRUD, `dashboard`, `files`, `import` | **login check only** |
| `V1/greeting` | `@has_access` → **302 HTML redirect** (not JSON) |

> **Known gap (decide at port):** a student with the `Tantangan Bebras Student` role can technically call question/event/student mutation endpoints (no role check). The frontend only restricts via sidebar visibility. Reproduce "as-is" or fix consistently — no half measures.

### 6.4 Roles

- FAB roles are created idempotently at startup: `Admin`, `Moderator`, `Course Creator`, `Tantangan Bebras Student` (+ `Batch Evaluator` by seed_demo). Legacy map: `volunter→Moderator`, `guru→Course Creator`.
- `UserProfile.app_role` defaults to `user`; **only** staff register writes `app_role` (`"user"`). UI flags (`isAdmin`, `isStudent`) are read from `roles[]` (FAB names), while backend gates read `app_role` → **two different sources of truth**.

---

## 7. Rate Limit (complete)

Default `60/minute` on all routes. Overrides:

| Route | Limit | Route | Limit |
|---|---|---|---|
| `POST /auth/register`, `POST /auth/login` | 5/m | `POST /student/auth/register` | 5/m |
| `POST /auth/logout` | 10/m | `POST /student/auth/login`, `/logout` | 10/m |
| `POST\|PATCH /topic`, `/topic/reorder` | 30/m | `DELETE /topic/<name>` | 10/m |
| `POST\|PATCH /question` | 30/m | `DELETE /question/<name>`, `/restore` | 10/m |
| `DELETE /question/<name>/purge` | 5/m | `POST /student/practice/create`, `/store` | 10/m |
| `POST /student/practice/answer-temp` | **120/m** | `POST\|PATCH /event` | 20/m |
| `DELETE /event/<name>`, `/restore` | 10/m | `DELETE /event/<name>/purge` | 5/m |
| `POST /student/event/make/<name>`, `/store` | 10/m | `POST /student/event/answer-temp` | 120/m |
| `POST /student`, `PATCH /student/<id>` | 20/m | `DELETE /student/<id>`, `/restore` | 10/m |
| `DELETE /student/<id>/purge` | 5/m | `POST /student/<id>/activate` | 30/m |
| `POST /student/import` | 5/m | `POST /users` | 10/m |
| `PATCH /users/<id>` | 20/m | `DELETE /users/<id>` | 10/m |
| `POST /files/upload`, `POST /todos`, `PUT /todos/<id>` | 30/m | `DELETE /todos/<id>` | 10/m |

---

## 8. Audit Logging

- `audit_log(action, user_id=, resource=, details=)` → `flush`; the API immediately `commit`s. On failure → `warning` + flush rollback (the business transaction is unaffected).
- 41 actions, naming pattern `{entity}_{event}`: `register_success/failure`, `login_success/failure`, `logout`, `topic_created/updated/deleted/reordered`, `question_created/updated/soft_deleted/restored/purged`, `practice_created/submitted`, `event_created/updated/soft_deleted/restored/purged`, `event_student_started/submitted`, `student_register_*`, `student_login_*`, `student_logout`, `student_created/updated/soft_deleted/restored/purged/activated`, `student_import`, `user_admin_created/updated/deleted`, `todo_created/updated/deleted`.
- `details.changed` = sorted keys of the changed fields (update). `resource` = `"{entity}/{name}"`.
- **Not audited:** all GETs, `files/upload`, `answer-temp`, `dashboard`, event results.

---

## 9. Scoring & Calculation Engine

**Correction (`_is_correct`, used by practice + event):**
```
if answer is empty                → wrong
if type == "Multiple Choice"      → lower(trim(answer)) == lower(correctAnswer)
else (Essay)                      → always wrong (no auto-grade)
```
**Submit:** `score = 10 × correct count` (max 100 with 10 MC questions). `timeLimit = int((finished − started).total_seconds())` if `startedAt` exists.

**Duration (client-only):** runner deadline = `startedAt + timeLimit × 60.000 ms` (practice fallback default 30 minutes; event fallback 0 = no countdown). **The backend never enforces a time limit** on `answer-temp`/`store`.

---

## 10. Error Contract

**Shape:** always `{"message": "<code>"}`.

**Pydantic validation formatter (`dto/_base.py`)** — only the **first** error:
`"{loc}_{message}"` where `loc` = the alias of the sent field (`questionType` vs `question_type` → different prefixes!), and the message from the map:

| Pydantic type | Result |
|---|---|
| `missing` | `{field}_required` |
| `string_too_short` | `{field}_must_be_at_least_{min}_characters` |
| `string_too_long` | `{field}_too_long` |
| `enum` / `literal_error` | `{field}_invalid` |
| `int_parsing` | `{field}_must_be_integer` |
| `greater_than_equal` | `{field}_must_be_at_least_{ge}` |
| `less_than_equal` | `{field}_must_be_at_most_{le}` |
| `email_parsing` | `{field}_invalid_email` |
| `extra_forbidden` | `{field}_unknown_field` |
| `value_error` (custom) | `{field}_{msg without the "Value error," prefix → lower + underscore}` |

A field validator whose message already carries the field name → **the field name is doubled** (`category_category_must_be_…`). A model validator (`mode=after`, empty loc) → literal `value_` prefix (`value_no_fields_to_update`, `value_pg_requires_option_a`).

**Fixed status codes:**
| Status | message |
|---|---|
| 401 | `unauthorized`, `invalid_credentials` |
| 403 | `forbidden` |
| 400 | DTO formatter result + `limit_or_offset_invalid`, `items_must_be_list`, `item_name_required`, `item_idx_invalid`, `items_malformed`, `*_name_required`, `no_file`, `file_required`, `missing_csrf_token`, `invalid_csrf_token` |
| 404/409 | service `ValueError` — **per-endpoint table in the domain specs** |
| 413 | `file_too_large: max 5 MB` |
| 429 | `rate_limit_exceeded` |

**Porting caveat:** there is no JSON 404/500 handler; an unknown GET `/api/*` hits the SPA catch-all → **200 HTML**.

---

## 11. Enum Catalog (Reference)

| Enum | Values |
|------|-------|
| Category (question/topic/event/student/practice) | `cub`, `scout`, `rover` (legacy: `siaga`, `penggalang`, `penegak`) |
| Difficulty level (`difficultyLevel` — legacy column `tingak_kesulitan`, sic) | `Easy`, `Medium`, `Hard` (legacy: `Mudah`, `Sedang`, `Sulit`) |
| Question type | `Multiple Choice`, `Essay` (legacy: `Pilihan Ganda`) |
| MC correct answer | `a`, `b`, `c`, `d` |
| Question status | `Active`, `Inactive` (legacy: `Aktif`, `Tidak Aktif`) |
| Student status | `Active`, `Inactive` |
| FAB role | `Admin`, `Moderator`, `Course Creator`, `Tantangan Bebras Student`, `Batch Evaluator` |
| `app_role` | `admin`, `moderator`, `course_creator`, `user` |
| User admin roles (DTO) | `Admin`, `Moderator`, `Course Creator` |
| Subscription tier (unused) | `community`, `premium`, `muhsinin` |

---

## 12. Cross-Feature Integration (Integration Matrix)

| Source | Target | Rule |
|--------|--------|--------|
| Question → Practice | pool | `category == student.category` AND `status == 'Active'` AND `disabled = false`; minimum `practiceMinQuestions` rows (settings, default 10) else 409 `insufficient_question_in_category: have {n}, need {min}` |
| Question → Event | create/update validation | all `questionsId` must exist (409 `question_not_found: a,b`), same category as the event (409 `question_category_mismatch: {name}`), not disabled (409 `question_disabled: {name}`) |
| Event → Attempt | `make` | guards `disabled` / `!published` / `eventDeadline passed` → 409; **category is not checked by the backend** |
| Student → Practice/Event | category | `student.category` determines the practice pool; event `categoryMatch` is only a UI gate |
| Student status → Login | `student/auth` | `status` is **not** checked at login — what is checked is `user.active` + `disabled`; activation = set `status='Active'` |
| Question soft delete → | pool/event | `disabled=true` is excluded from default lists & blocked from events |
| xlsx import → | student | upsert per username; email conflict with a different username → row error |
| All mutations → | audit_logs | `audit_log(...)` then `commit` in the API layer |
| Dashboard → | counters | raw aggregation (see spec 06 §2.1 — **no disabled filter** for questions/events/students) |

---

## 13. UI Navigation Map

| Role | Page (route name) |
|------|----------------------|
| Public | `login`, `student-login`, `student-register` |
| All logged in | `home`, `todos` |
| Staff (desktop) | `question`, `question-new`, `question-editor`, `question-detail`, `question-edit`, `event`, `event-new`, `event-detail`, `event-edit`, `event-results`, `practice-admin`, `practice-admin-detail`, `student`, `student-new`, `student-import`, `student-detail`, `student-edit`, `users`, `users-new`, `users-detail`, `users-edit`, `dashboard-admin` |
| Student | `student-dashboard`, `practice`, `practice-start`, `practice-detail`, `event-student`, `event-student-start`, `event-student-result` |

Guard: `meta.public` passes; login required → revalidate → redirect `login?redirect=…`. **`meta.role` is declarative only, not executed.** Mobile: the sidebar is trimmed (staff: Home+Question; student: Home+Practice+Event). Per-page step details: §UI Flow in each domain spec.

---

## 14. Porting Decisions (Hazard Register)

Behaviors that **must be deliberately reproduced** or **consciously fixed** — they must never happen by accident:

1. **Weak RBAC** on Tantangan Bebras mutations (§6.3) — `_author_or_mod` never rejects.
2. **`app_role` vs FAB role are separate** — `_is_admin()` fails for a user that only has the FAB `Admin` role.
3. **`eventQuestionId` mixed key-space** — the client receives `event_student_question` ids but writes them into the FK column `event_question.id` (autosave); on strict-FK Postgres it can fail; PATCH event renumbers the ids.
4. **Naive vs aware datetime** in the `event_expired` guard → `TypeError` on Postgres.
5. **Inconsistent status codes**: event update `event_not_found` → 409; practice `answer-temp` after submit → 404; `activate` while disabled → 404; practice create `student_not_found` → 409.
6. **`QuestionUpdate` without MC/Essay business validation** → type transitions can create inconsistent rows.
7. **`total` ≠ `items`** on `GET /question` (total ignores the `difficultyLevel`/`topicId`/`q` filters).
8. **Attempt PK based on timestamp** → a collision within 1 second = 500.
9. **No backend time limit** after an attempt is created; `published`/`deadline` are not re-checked on `start`/`store`.
10. **N+1** on the event list & dashboard `recentEvents`; the event-student offset is applied after the 500 cap.
11. **Admin login ignores `user.active`**; a hard user delete orphans `student`/`user_profile`.
12. **Serialization inconsistency** of timestamps (with/without timezone).
13. The SPA catch-all swallows API 404s (GET → 200 HTML).
14. Dead code: `require_role` import, `TopicReorderItem`, the subscription DTO, `StudentAuthService._slugify`, the reorder UI no-op, etc.

---

## 15. Glossary

| Term | Definition |
|---------|----------|
| Staff | Non-student user (Admin/Moderator/Course Creator/user) logging in via `/auth` |
| Student | A `student` row above `ab_user`; logs in via `student/auth` |
| Practice sheet | One `practice` = 10 random questions for one student |
| Attempt | One `event_student` = one event participation (unique per student+event) |
| Before/after shuffle | Record of the question order before & after shuffling (fairness audit) |
| Autosave | `*_answer_temp` upsert per answer, rate 120/minute |
| `name` (PK) | Natural string key (slug) replacing UUIDs in the main Tantangan Bebras tables |
| Soft delete | `disabled`+`disabled_at`; the row still exists, hidden from lists |
| `app_role` | Authorization role in `user_profile` (read by backend gates) |
| Category match | `event.category == student.category` — gate for the Start button in the UI |

---

**Next:** [`01-auth-student-users.md`](01-auth-student-users.md) — Staff Auth, Student Auth, User Admin.
