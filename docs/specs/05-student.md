# 05 — Student (Management & Import)

> Parent: [`00-master-overview.md`](00-master-overview.md)
> Scope: `student` (discriminator above `ab_user`), API `/api/v1/student`, XLSX import, activation.

---

## 1. Entity & Tables

### 1.1 `student`

| Column | Type | Notes |
|-------|------|-------|
| `user_id` | INTEGER **PK** → `ab_user.id` CASCADE | not autoincrement — the FK doubles as PK |
| `category` | VARCHAR(20) NOT NULL default `'cub'` | `cub`/`scout`/`rover`; index `(category,status)` |
| `school` | VARCHAR(140) nullable | |
| `city` | VARCHAR(80) nullable | |
| `country` | VARCHAR(80) nullable default `'Indonesia'` | |
| `status` | VARCHAR(20) NOT NULL default `'Inactive'` | `Active`/`Inactive`; index |
| `disabled` | BOOLEAN default 0 | soft delete; index |
| `disabled_at` | DATETIME nullable | |
| `created_at`, `updated_at` | DATETIME default now | |

**Relation:** a mandatory row above `ab_user` (PK = `user_id`). Soft delete **also** sets `ab_user.active = false` (and restore sets it back). `status` is only a data/activation marker; **what blocks student login is `user.active` + `disabled`**.

Enum: `STUDENT_STATUS = ("Active", "Inactive")`.

---

## 2. Flow: Student CRUD Admin (`/api/v1/student`)

All endpoints **only check login** (no role — hazard 00 §6.3).

### 2.1 `GET /` (list)

`limit` 100 (1..200) · `offset ≥0` · 400 `limit_or_offset_invalid`.
Filters: `category`, `status`, `q` (ilike over `username, email, first_name, last_name, school`), `includeDisabled` truthy (hide `disabled` by default).
Query joins `ab_user` — **rows without a user are skipped** → `len(items)` can be < `total`. Order `created_at DESC`. → **200** `{ items, total }`.

### 2.2 `POST /` — rate 20/minute

1. `StudentCreate`: `firstName`/`lastName` required (no length limit); `email` valid (`@` + `.` after `@`); `username` 3..80; `password` min 6; `category` enum; `status` enum **default `"Inactive"`**; `country` default `"Indonesia"`; `school`/`city` optional; `emailVerifiedAt` optional ISO string.
2. Service — `ValueError` → **409**:
   - `username.strip()` duplicate → `username_already_registered`;
   - `email.strip().lower()` duplicate → `email_already_registered`;
   - insert `User(username, email, first/last as-is — **not stripped**, hash, active=True)`;
   - `emailVerifiedAt` when present → parse ISO (`Z`→`+00:00`); failure → `email_verified_at_invalid`;
   - attach the FAB role `Tantangan Bebras Student` (**if the role is missing it is silently skipped**);
   - flush → `IntegrityError` → rollback → `username_or_email_taken`;
   - insert `Student(category, school, city, country, status)` → commit.
3. Audit `student_created` `details={"category","status"}` → commit → **201** `StudentOut`.

### 2.3 `GET /<user_id>`

Missing student → 404 `student_not_found`. ⚠ When `ab_user` is missing, `from_student(student, user=None)` → **AttributeError/500** (the list skips, the detail does not).

### 2.4 `PATCH /<user_id>` — rate 20/minute

`StudentUpdate` (optional, `extra="ignore"`, empty → `value_no_fields_to_update`). Error mapping: `404 if "not_found" in message else 409`:
- user/student missing → `student_not_found` → **404**; username duplicate (only when changed) → `username_already_registered` → **409**.
- Application order: `firstName→first_name`, `lastName→last_name`, `email→email = strip().lower()` (⚠ **`username` is not synced**), `username` (duplicate checked first), `password` truthy → rehash; then `student` fields: `category/school/city/country/status` when sent → commit.
- Audit `student_updated` `details.changed` → **200** `StudentOut`.

### 2.5 `DELETE /<user_id>` — rate 10/minute (**soft**)

Missing user/student → 404. `student.disabled=True; disabled_at=utcnow(); user.active=False` → commit → audit `student_soft_deleted` → **204**.

### 2.6 `POST /<user_id>/restore` — 10/minute

404 `student_not_found`; `disabled=False; disabled_at=None; user.active=True` (user may be None → skipped) → audit `student_restored` → **200** `StudentOut`.

### 2.7 `POST /<user_id>/activate` — rate 30/minute

All `ValueError` → **404** (not 409):
- student missing → `student_not_found`;
- `student.disabled` → **`student_disabled`** (a soft-deleted row cannot be activated — `restore` first);
- else → `student.status = "Active"` (**does not** touch `disabled`/`user.active`) → commit → audit `student_activated` → **200** `StudentOut`.

### 2.8 `DELETE /<user_id>/purge` — rate 5/minute (**hard**)

When both are missing → 404. **Order: delete `Student` first, then `User`** (no ORM cascade; relies on the DB FK) → commit → audit `student_purged` → **204**. Attempts/practices are deleted via `ON DELETE CASCADE` on `ab_user.id`.

### 2.9 `StudentOut` shape

`{ userId, username, email, firstName, lastName, category, school, city, country, status, disabled, disabledAt, createdAt }` — **no `updatedAt`** (the presenter does not serialize that column). `firstName`/`lastName` come from `ab_user.first_name`/`last_name`, `username` from `ab_user`.

---

## 3. Flow: XLSX Import

### 3.1 Endpoint

- `POST /api/v1/student/import` — rate **5/minute**. Without a `file` part → **400** `{message:"file_required"}` (checked before the service). Success/error workbook → audit `student_import` `details={"inserted","updated","errors":len}` → **200** `{ inserted: int, updated: int, errors: [{row, message}] }` — **never 4xx for a broken workbook**.
- `GET /api/v1/student/import-template` — login only → a binary xlsx Response, header `Content-Disposition: attachment; filename="student-import-template.xlsx"`.

### 3.2 Column contract

```
REQUIRED: first_name, last_name, email, username, password, category
OPTIONAL: school, city, country, status
```
- Header normalization: `strip().lower().replace(" ","_")`; empty headers are skipped; duplicate headers → **the last index wins**.
- Data starts at `min_row=2`; fully-empty rows are skipped; cell values → `"" if None else str(value).strip()` (xlsx float numbers become `"12345.0"`).

### 3.3 File-level errors (returned as `errors[0]` with `row=0`, never an exception)

| Condition | message |
|---|---|
| no file / empty filename | `file_required` |
| `load_workbook` failed | `xlsx_unreadable: {exc}` |
| no active sheet | `xlsx_empty_sheet` |
| first row empty | `xlsx_missing_header` |
| required columns missing | `missing_required_columns: {a,b,c}` (in `REQUIRED_COLUMNS` order) |
| header OK but 0 data rows | `no_data_rows` |

### 3.4 Template workbook

Sheet `student`; header = all columns; 1 sample row: `Budi | Santoso | budi@example.test | budi | Siswa1234 | scout | SMPN 1 Bandung | Bandung | Indonesia | Inactive`.

### 3.5 Row loop (number = the Excel row, starting at 2)

1. Build the `StudentCreate` payload: `country` default `"Indonesia"`; `status = _resolve_status(raw)` — lowercased ∈ `{"aktif","active","1","true","yes"}` → `"Active"`, else → **`"Inactive"`**.
   Pydantic validation failure → `{"row": n, "message": "validation: {exc}"}` (multi-line Pydantic repr, **not** the formatter) → continue to the next row.
2. Conflict check: `existing_email` (by email) exists and its `username` differs from the payload → `email_already_registered` → skip; `existing_user` (by username) exists without `existing_email` → `username_already_registered` → skip.
3. **Update mode** (username matches): `svc.update(user.id, {firstName, lastName, email, category, school, city, country, status})` — ⚠ the **password is NOT updated**; `ValueError` → the message is appended; `updated += 1`.
4. **Create mode**: `svc.create(payload)`; `ValueError` → the message is appended; `inserted += 1`.

### 3.6 UI usage

`StudentImportView` sends `FormData` via `fetchJson` which does `JSON.stringify` → **the file most likely never arrives** (a frontend flaw, hazard — see §5.4).

---

## 4. Error Catalog

| Code | message |
|------|---------|
| 400 | `file_required` (import without a file), `firstName_required`, `username_must_be_at_least_3_characters`, `password_must_be_at_least_6_characters`, `status_status_invalid`, `category_category_must_be_cub_scout_or_rover`, `email_invalid_email`, `value_no_fields_to_update`, `limit_or_offset_invalid` |
| 401 | `unauthorized` |
| 404 | `student_not_found` (get/delete/restore/purge/activate) · **`student_disabled`** (activate while disabled) · `student_not_found` (update, via the substring mapping) |
| 409 | `username_already_registered`, `email_already_registered`, `email_verified_at_invalid`, `username_or_email_taken` (create) · `username_already_registered` (update) |
| 429 | `rate_limit_exceeded` |

---

## 5. UI Flow (Vue)

### 5.1 List — `/student` (`student`)

- Header: **Import** (outline) → `student-import`; **Add Student** (solid) → `student-new`.
- Toolbar: search (client-side: email, `firstName lastName`, school); **statusFilter default `'Active'`** — options are only `Active` / `Not Active ('Inactive')`, **no "all" option**; categoryFilter (`''` + 3 categories).
- `status`+`category` → **server-side** (`GET /student?status&category`), watch debounce 200 ms; `searchTerm` is not watched (client-side only).
- Columns: Name · School (from `item.school`, `—` when empty) · Category (blue badge) · Status (green `Active` badge / orange raw value) · Actions. Hidden below `md`: School + Status.
- Row actions: **Activate** (ghost green, **only when `status === 'Inactive'`**) → `POST /student/{id}/activate` → replace the row + toast; **Edit** → the form; **Delete** → `dialog.danger` "Delete Student" → `DELETE` → filter + toast.
- Empty: "No students yet — add a student or import from CSV." + a button.

### 5.2 Form — `/student/new`, `/student/:userId/edit`

- Defaults: `category:'cub'`, **`status:'Inactive'`**, `country:'Indonesia'`.
- Edit: load `GET /student/{userId}` (school/city fallback `''`).
- Conditionals: **Username `disabled` on edit**, `minlength=3`; **Password**: create → required `minlength=6`; edit → "New Password (optional)" not required; the status select literal `Inactive`, `Active`.
- Edit submit → `PATCH {firstName, lastName, email, category, school?, city?, country?, status, password?}` (⚠ **username is not sent**) → `/student/{userId}`; create → `POST {..., username, password}` → `/student`. On failure → inline `error`.

### 5.3 Detail — `/student/:userId`

Load `GET /student/{userId}` (no try/catch — a failure leaves "Loading…" forever). Name; sub `{CATEGORY_LABELS[category]} • {status}`; cards for Email/Username/School/City/Country (`?? '—'`); links **Edit** & **Back**.

### 5.4 Import — `/student/import`

Copy: *"Upload an xlsx file. Expected columns: `first_name, last_name, email, username, password, category, school, city, country`"*. `<input accept=".xlsx">`; the upload button is `disabled` until a file is selected; submit → result `Success: {inserted} inserted, {updated} updated` + a red list `Row {row}: {message}`; on failure → `error`.
⚠ Known bug: `fetchJson` does `JSON.stringify` on the FormData → the request most likely yields `file_required` — fix at this point when wiring it up (see `services/api.ts`).

### 5.5 Related user detail card (cross-reference)

`/users/:id` shows a **"Student Data"** card when `user.student` exists: a category badge, status (green `Active` / orange), school/city/country rows.
